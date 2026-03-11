"""
Telegram bot - Webhook orqali komandalar (sinxron).
"""
import logging
import requests
from django.conf import settings

from .services import required_channels_ok_for_telegram_id
from .models import RequiredChannel

logger = logging.getLogger(__name__)
WEBAPP_URL = getattr(settings, "TELEGRAM_WEBAPP_URL", "").rstrip("/")


def _send_message(chat_id: int, text: str, reply_markup: dict | None = None) -> bool:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:  # pragma: no cover - tarmoq xatolari
        logger.warning("Telegram send_message failed: %s", e)
        return False


def _web_app_keyboard() -> dict | None:
    """Mini App ochish tugmasi."""
    if not WEBAPP_URL:
        return None
    return {
        "keyboard": [
            [{"text": "💰 Chiqimlarni ochish", "web_app": {"url": WEBAPP_URL}}]
        ],
        "resize_keyboard": True,
    }


def _required_channels_text() -> str:
    """
    Majburiy kanallar ro'yxatini foydalanuvchiga ko'rsatish matni.
    """
    channels = RequiredChannel.objects.filter(is_active=True, is_mandatory=True)
    if not channels.exists():
        return (
            "Ilova uchun hozir majburiy kanal yo'q. Agar bu xabarni ko'rsangiz, iltimos, /start ni qayta yuboring."
        )
    lines: list[str] = ["Ilovadan foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling:", ""]
    for ch in channels:
        username = (ch.username or "").strip()
        if not username:
            continue
        if not username.startswith("@"):
            username = "@" + username
        lines.append(f"• {ch.name}: {username}")
    lines.append("")
    lines.append("Obuna bo'lgandan keyin /start deb yozing va Mini App tugmasi chiqadi.")
    return "\n".join(lines)


def handle_start(chat_id: int, first_name: str = "") -> bool:
    """/start - Mini App tugmasi (avtologin, kanal obunasi shart)."""
    # Avval foydalanuvchi majburiy kanallarga obuna bo'lganini tekshiramiz.
    if not required_channels_ok_for_telegram_id(chat_id):
        text = _required_channels_text()
        _send_message(chat_id, text)
        return True

    safe_name = first_name or "do'st"
    text = (
        f"Salom, {safe_name}! 👋\n\n"
        "Pastdagi <b>«Chiqimlarni ochish»</b> tugmasini bosing — ilova ochiladi va siz avtomatik kirasiz. "
        "Ro'yxatdan o'tish ham, kod kiritish ham shart emas. Faqat Telegram profilingiz asosida kirasiz."
    )
    _send_message(chat_id, text, reply_markup=_web_app_keyboard())
    return True


def handle_help(chat_id: int) -> bool:
    text = (
        "📌 Buyruqlar:\n"
        "/start — «Chiqimlarni ochish» tugmasi (Mini App avtologin)\n"
        "/help — Yordam\n"
        "/donat — Donat usullari va linklar\n\n"
        "Ilovani ochish: pastdagi tugmani bosing — kod yoki alohida ro'yxatdan o'tish talab qilinmaydi."
    )
    _send_message(chat_id, text)
    return True


def handle_donate(chat_id: int) -> bool:
    """Donat usullari ro'yxati va linklar."""
    from accounts.models import DonationMethod

    methods = DonationMethod.objects.filter(is_active=True).order_by("sort_order", "id")
    if not methods.exists():
        text = "Hozircha donat usullari qo'shilmagan. Keyinroq qayta urinib ko'ring."
        _send_message(chat_id, text)
        return True
    lines = ["⭐ <b>Donater bo'ling</b>\n", "Ilovani rivojlantirishga yordam bering. To'liq moliyaviy tushunchalar va 12 oylik statistika donat qilganlar uchun. Quyidagi usullar orqali donat qilishingiz mumkin:\n"]
    for m in methods:
        if m.payment_link:
            lines.append(f"• <b>{m.title}</b>\n{m.payment_link}")
    lines.append("\nRahmat! Donat qilgandan keyin donater statusi admin tomonidan tasdiqlanadi.")
    _send_message(chat_id, "\n".join(lines))
    return True


def process_update(update_dict: dict) -> None:
    """Webhook update ni qayta ishlash."""
    message = update_dict.get("message") or {}
    text = (message.get("text") or "").strip()
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return
    user = message.get("from") or {}
    first_name = user.get("first_name", "")
    if text == "/start":
        handle_start(chat_id, first_name)
    elif text == "/help":
        handle_help(chat_id)
    elif text == "/donat":
        handle_donate(chat_id)

