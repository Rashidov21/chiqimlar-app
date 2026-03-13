import logging
from typing import Optional

import requests
from django.conf import settings
from django.core.cache import cache

from .models import RequiredChannel

logger = logging.getLogger(__name__)


def _get_bot_token() -> Optional[str]:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token:
        logger.warning("telegram_bot.services: TELEGRAM_BOT_TOKEN yo'q, kanal obunasi tekshirilmaydi.")
    return token


def _telegram_api_request(method: str, params: dict) -> Optional[dict]:
    token = _get_bot_token()
    if not token:
        return None
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            logger.warning("Telegram API %s failed status=%s body=%s", method, resp.status_code, resp.text)
            return None
        data = resp.json()
        if not data.get("ok"):
            logger.warning("Telegram API %s ok=False body=%s", method, data)
            return None
        return data.get("result")
    except Exception as e:
        logger.warning("Telegram API %s exception: %s", method, e)
        return None


def _get_chat_member_status(chat_identifier: str | int, user_id: int) -> Optional[str]:
    """
    getChatMember orqali user statusini qaytaradi (member, administrator, creator, left, kicked, ...).
    chat_identifier: channel_id yoki @username.
    """
    result = _telegram_api_request(
        "getChatMember",
        {"chat_id": chat_identifier, "user_id": user_id},
    )
    if not result:
        return None
    return result.get("status")


SUBSCRIPTION_CACHE_TTL = 600  # sekund, kanal obunasi holati uchun cache


def is_member_of_required_channel(telegram_id: int, channel: RequiredChannel) -> bool:
    """
    Bitta RequiredChannel uchun foydalanuvchi obunasini tekshiradi (cache bilan).
    """
    if not telegram_id:
        return False

    cache_key = f"sub:{telegram_id}:{channel.pk}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    chat_identifier: str | int
    if channel.channel_id:
        chat_identifier = channel.channel_id
    else:
        username = channel.username.strip()
        if not username:
            logger.warning("RequiredChannel pk=%s da username yo'q.", channel.pk)
            cache.set(cache_key, False, SUBSCRIPTION_CACHE_TTL)
            return False
        if not username.startswith("@"):
            username = "@" + username
        chat_identifier = username

    status = _get_chat_member_status(chat_identifier, telegram_id)
    ok = status in {"member", "administrator", "creator"}
    cache.set(cache_key, ok, SUBSCRIPTION_CACHE_TTL)
    return ok


def required_channels_ok_for_telegram_id(telegram_id: int) -> bool:
    """
    Foydalanuvchi barcha active+mandatory kanallarga obuna bo'lganmi?
    Hech qanday majburiy kanal bo'lmasa, True.
    """
    if not telegram_id:
        return False

    channels = RequiredChannel.objects.filter(is_active=True, is_mandatory=True)
    if not channels.exists():
        return True

    for ch in channels:
        if not is_member_of_required_channel(telegram_id, ch):
            return False
    return True


def clear_subscription_cache_for_user(telegram_id: int) -> None:
    """
    Berilgan Telegram ID uchun kanal obunasi cache'ini tozalaydi.
    Faqat SUBSCRIPTION_CACHE_TTL bilan saqlanadigan kalitlarni o'chiradi.
    """
    if not telegram_id:
        return
    for ch in RequiredChannel.objects.all():
        cache_key = f"sub:{telegram_id}:{ch.pk}"
        cache.delete(cache_key)

