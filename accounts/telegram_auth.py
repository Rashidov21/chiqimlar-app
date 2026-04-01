"""
Telegram Mini App initData tekshirish va user aniqlash.
Signature verification, timestamp tolerance, replay himoya.
"""
import hmac
import hashlib
import json
import logging
from urllib.parse import unquote

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

REPLAY_CACHE_KEY_PREFIX = "tg_initdata:"
REPLAY_CACHE_TTL = 300  # 5 daqiqa - bir xil init_data qayta ishlatilmasin


def replay_cache_key(init_hash: str) -> str:
    return f"{REPLAY_CACHE_KEY_PREFIX}{init_hash}"


def validate_telegram_init_data(init_data: str) -> dict | None:
    """
    Telegram WebApp initData ni tekshiradi.
    To'g'ri bo'lsa user ma'lumotlarini qaytaradi, aks holda None.
    """
    if not init_data:
        logger.warning("tg_init_data: init_data bo'sh")
        return None
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token:
        logger.warning("tg_init_data: TELEGRAM_BOT_TOKEN sozlanmagan")
        return None
    try:
        parsed = {}
        for part in init_data.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                parsed[k] = unquote(v)
        if "hash" not in parsed:
            logger.warning("tg_init_data: hash yo'q")
            return None

        # Vaqt cheklovi: auth_date juda eski bo'lmasligi kerak
        max_age = int(getattr(settings, "TELEGRAM_INITDATA_MAX_AGE", 86400))
        auth_date_raw = parsed.get("auth_date") or parsed.get("auth_timestamp")
        if auth_date_raw:
            try:
                auth_ts = int(auth_date_raw)
                now_ts = int(timezone.now().timestamp())
                if now_ts - auth_ts > max_age:
                    logger.warning(
                        "tg_init_data: auth_date eskirgan (max_age=%s, diff=%s)",
                        max_age,
                        now_ts - auth_ts,
                    )
                    return None
            except (TypeError, ValueError):
                logger.warning("tg_init_data: auth_date parse xato")
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
            logger.warning("tg_init_data: hash mos kelmadi (token boshqa botga tegishli bo'lishi mumkin)")
            return None

        if "user" in parsed:
            user_data = json.loads(parsed["user"])
            user_data["_init_hash"] = received_hash
            return user_data
        logger.warning("tg_init_data: user maydoni yo'q")
        return None
    except Exception as e:
        logger.warning("tg_init_data: xato %s", type(e).__name__, exc_info=True)
        return None
