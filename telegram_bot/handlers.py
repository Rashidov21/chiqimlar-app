"""
Telegram bot - Webhook orqali komandalar (sinxron).
"""
import logging
import requests
from django.conf import settings

from accounts.models import VerificationCode

logger = logging.getLogger(__name__)
WEBAPP_URL = getattr(settings, "TELEGRAM_WEBAPP_URL", "").rstrip("/")


def _send_message(chat_id: int, text: str) -> bool:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        logger.warning("Telegram send_message failed: %s", e)
        return False


def handle_start(chat_id: int, first_name: str = ""):
    """/start - Tasdiqlash kodi yuborish va veb-ilova tugmasi."""
    vc = VerificationCode.generate(chat_id)
    minutes = getattr(settings, "VERIFICATION_CODE_EXPIRE_MINUTES", 10)
    text = (
        f"Salom, {first_name or 'do\'st'}! 👋\n\n"
        f"Veb-ilovaga kirish uchun tasdiqlash kodingiz:\n\n"
        f"🔑 {vc.code}\n\n"
        f"Kod {minutes} daqiqa amal qiladi.\n\n"
        f"Veb-ilovani ochish: {WEBAPP_URL}/"
    )
    _send_message(chat_id, text)
    # Inline button requires reply_markup; for simplicity we just send URL in text
    return True


def handle_code(chat_id: int):
    """Yangi tasdiqlash kodi."""
    vc = VerificationCode.generate(chat_id)
    text = (
        f"Yangi tasdiqlash kodingiz:\n\n"
        f"🔑 {vc.code}\n\n"
        f"Veb-ilovada kirish oynasiga bu kodni kiriting."
    )
    _send_message(chat_id, text)
    return True


def handle_help(chat_id: int):
    text = (
        "📌 Buyruqlar:\n"
        "/start — Kirish kodi olish va veb-ilova linki\n"
        "/code — Yangi kirish kodi olish\n"
        "/help — Yordam\n\n"
        "Veb-ilovada xarajatlaringizni kiritishingiz, byudjet va statistikani ko'rishingiz mumkin."
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
    elif text == "/code":
        handle_code(chat_id)
    elif text == "/help":
        handle_help(chat_id)
