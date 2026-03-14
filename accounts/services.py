"""
Hisoblar - Biznes logikasi (tasdiqlash kodi, rate limit, Telegram login token).
"""
import secrets
import time

from django.utils import timezone
from django.core.cache import cache

from .models import User, VerificationCode


RATE_LIMIT_KEY_PREFIX = "verify_code:"
RATE_LIMIT_WINDOW = 60  # soniya
RATE_LIMIT_MAX = 5

TELEGRAM_LOGIN_TOKEN_PREFIX = "tg_login_token:"
TELEGRAM_LOGIN_TOKEN_TTL = 300  # soniya, 5 daqiqa ichida foydalanilishi kerak


def check_rate_limit(identifier: str) -> bool:
    """Kod so'rovlari uchun rate limit."""
    key = f"{RATE_LIMIT_KEY_PREFIX}{identifier}"
    data = cache.get(key) or {"count": 0, "start": time.time()}
    now = time.time()
    if now - data["start"] > RATE_LIMIT_WINDOW:
        data = {"count": 0, "start": now}
    data["count"] += 1
    cache.set(key, data, timeout=RATE_LIMIT_WINDOW)
    return data["count"] <= RATE_LIMIT_MAX


def generate_telegram_login_token(telegram_id: int) -> str:
    """
    Telegram login uchun bir martalik token yaratadi.
    Token cache'da saqlanadi va faqat bir marta ishlatiladi.
    """
    if not telegram_id:
        raise ValueError("telegram_id bo'sh bo'lishi mumkin emas")
    # token_urlsafe 16 ~ 22 belgili bo'ladi, URL uchun qulay
    token = secrets.token_urlsafe(16)
    cache_key = f"{TELEGRAM_LOGIN_TOKEN_PREFIX}{token}"
    cache.set(
        cache_key,
        {"telegram_id": telegram_id, "created_at": int(time.time())},
        timeout=TELEGRAM_LOGIN_TOKEN_TTL,
    )
    return token


def consume_telegram_login_token(token: str) -> int | None:
    """
    Tokenni o'qib, bir marta foydalanilgandan so'ng o'chiradi.
    To'g'ri bo'lsa telegram_id qaytaradi, aks holda None.
    """
    if not token:
        return None
    cache_key = f"{TELEGRAM_LOGIN_TOKEN_PREFIX}{token}"
    data = cache.get(cache_key)
    if not data or "telegram_id" not in data:
        return None
    cache.delete(cache_key)
    return int(data["telegram_id"])


def get_or_create_user_by_telegram(telegram_id: int, username: str = None, first_name: str = None) -> User:
    """Telegram ID bo'yicha foydalanuvchini topadi yoki yaratadi."""
    user = User.objects.filter(telegram_id=telegram_id).first()
    if user:
        # Mavjud foydalanuvchining ismini yangilash (agar o'zgargan bo'lsa)
        new_first_name = (first_name or "").strip()
        if new_first_name and user.first_name != new_first_name:
            user.first_name = new_first_name
            user.save(update_fields=["first_name"])
        return user
    username_base = f"tg_{telegram_id}"
    username = username_base
    counter = 0
    while User.objects.filter(username=username).exists():
        counter += 1
        username = f"{username_base}_{counter}"
    user = User.objects.create_user(
        username=username,
        telegram_id=telegram_id,
        first_name=first_name or "",
    )
    return user


def verify_code_and_login(code: str, request) -> tuple[User | None, str]:
    """
    Kodni tekshiradi va foydalanuvchini login qiladi.
    Qaytadi: (user yoki None, xabar)
    """
    code = (code or "").strip().upper()
    if not code or len(code) != 6:
        return None, "Kod 6 ta belgidan iborat bo'lishi kerak."

    if not check_rate_limit(f"code_{code}"):
        return None, "Juda ko'p urinish. Bir daqiqadan keyin qaytadan urinib ko'ring."

    vc = VerificationCode.objects.filter(
        code=code, is_used=False
    ).select_related("user").order_by("-created_at").first()

    if not vc:
        return None, "Noto'g'ri yoki muddati o'tgan kod."

    if not vc.is_valid():
        return None, "Kod ishlatilgan yoki muddati tugagan."

    user = vc.user
    if not user:
        user = get_or_create_user_by_telegram(vc.telegram_id)
        vc.user = user
        vc.save(update_fields=["user"])

    vc.is_used = True
    vc.save(update_fields=["is_used"])

    from django.contrib.auth import login
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return user, "Muvaffaqiyatli kirdingiz."
