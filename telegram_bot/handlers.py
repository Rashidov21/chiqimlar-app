"""
Telegram bot - Webhook orqali komandalar (sinxron).
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)
WEBAPP_URL = getattr(settings, "TELEGRAM_WEBAPP_URL", "").rstrip("/")


def _send_message(chat_id: int, text: str, reply_markup: dict = None) -> bool:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        logger.warning("Telegram send_message failed: %s", e)
        return False


def _web_app_keyboard():
    """Mini App ochish tugmasi."""
    if not WEBAPP_URL:
        return None
    return {
        "keyboard": [
            [{"text": "💰 Chiqimlarni ochish", "web_app": {"url": WEBAPP_URL}}]
        ],
        "resize_keyboard": True,
    }


def handle_start(chat_id: int, first_name: str = ""):
    """/start - Mini App tugmasi (avtologin)."""
    text = (
        f"Salom, {first_name or 'do\'st'}! 👋\n\n"
        f"Pastdagi <b>«Chiqimlarni ochish»</b> tugmasini bosing — ilova ochiladi va siz avtomatik kirasiz. "
        f"Ro'yxatdan o'tish ham, kod kiritish ham shart emas. Faqat Telegram profilingiz asosida kirasiz."
    )
    _send_message(chat_id, text, reply_markup=_web_app_keyboard())
    return True


def handle_help(chat_id: int):
    text = (
        "📌 Buyruqlar:\n"
        "/start — «Chiqimlarni ochish» tugmasi (Mini App avtologin)\n"
        "/help — Yordam\n\n"
        "Ilovani ochish: pastdagi tugmani bosing — kod yoki alohida ro'yxatdan o'tish talab qilinmaydi."
    )
    _send_message(chat_id, text)
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
