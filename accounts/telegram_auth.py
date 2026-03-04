"""
Telegram Mini App initData tekshirish va user aniqlash.
"""
import hmac
import hashlib
import json
from urllib.parse import parse_qs, unquote

from django.conf import settings


def validate_telegram_init_data(init_data: str) -> dict | None:
    """
    Telegram WebApp initData ni tekshiradi.
    To'g'ri bo'lsa user ma'lumotlarini qaytaradi, aks holda None.
    """
    if not init_data or not getattr(settings, "TELEGRAM_BOT_TOKEN", None):
        return None
    token = settings.TELEGRAM_BOT_TOKEN
    try:
        parsed = {}
        for part in init_data.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                parsed[k] = unquote(v)
        if "hash" not in parsed:
            return None
        received_hash = parsed.pop("hash")
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(
            b"WebAppData",
            token.encode(),
            hashlib.sha256,
        ).digest()
        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(computed_hash, received_hash):
            return None
        if "user" in parsed:
            user_data = json.loads(parsed["user"])
            return user_data
        return None
    except Exception:
        return None
