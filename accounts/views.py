"""
Hisoblar - Login, ro'yxatdan o'tish (Telegram orqali), chiqish, Telegram Mini App auth.
"""
import logging
from urllib.parse import urlparse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings

from core.rate_limit import rate_limit_ip
from .services import get_or_create_user_by_telegram, check_rate_limit
from telegram_bot.services import required_channels_ok_for_telegram_id
from .telegram_auth import validate_telegram_init_data

logger = logging.getLogger(__name__)


def _is_allowed_auth_origin(request) -> bool:
    """
    CSRF exempt endpoint uchun qo'shimcha himoya:
    Origin/Referer bo'lsa, host biznikiga mos bo'lishi kerak.
    """
    origin = request.headers.get("Origin")
    referer = request.headers.get("Referer")
    source = origin or referer
    if not source:
        return True
    try:
        parsed = urlparse(source)
        source_hostname = parsed.hostname
    except Exception:
        return False
    request_host = request.get_host().split(":")[0]
    allowed_hosts = set(getattr(settings, "ALLOWED_HOSTS", []))
    return source_hostname == request_host or source_hostname in allowed_hosts


@require_http_methods(["GET", "HEAD"])
def login_view(request):
    """
    Login sahifasi endi faqat ma'lumot beruvchi ekran:
    - Telegram Mini App orqali kelganda initData bilan avtologin ishlaydi.
    - Brauzer foydalanuvchisi uchun esa botga /start yuborib, «Chiqimlarni ochish» tugmasidan
      foydalanish bo'yicha ko'rsatmalar chiqadi.
    """
    if request.user.is_authenticated:
        return redirect("expenses:dashboard")
    return render(request, "accounts/login.html")


@require_http_methods(["GET", "HEAD"])
def register_view(request):
    """
    Ro'yxatdan o'tish sahifasi: endi alohida forma yo'q.
    Foydalanuvchi botga /start yuborib, Mini App orqali avtomatik yaratiladi.
    """
    if request.user.is_authenticated:
        return redirect("expenses:dashboard")
    return render(request, "accounts/register.html")


@require_http_methods(["POST"])
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Siz tizimdan chiqdingiz.")
    return redirect("accounts:login")


@login_required
def settings_view(request):
    return redirect("expenses:settings")


@csrf_exempt
@require_POST
@rate_limit_ip("telegram_webapp_auth", window=60, max_requests=20)
def telegram_webapp_auth(request):
    """
    Telegram Mini App: initData orqali avtomatik login.
    POST: init_data=<Telegram.WebApp.initData>
    """
    if not _is_allowed_auth_origin(request):
        logger.warning("tg_webapp_auth: forbidden_origin")
        return JsonResponse({"ok": False, "error": "forbidden_origin"}, status=403)

    init_data = request.POST.get("init_data", "").strip()
    if not init_data and request.body:
        try:
            import json as _json
            data = _json.loads(request.body)
            init_data = data.get("init_data", "")
        except Exception:
            pass
    user_data = validate_telegram_init_data(init_data)
    if not user_data:
        logger.warning("tg_webapp_auth: invalid_init_data (validate_telegram_init_data returned None)")
        return JsonResponse({"ok": False, "error": "invalid_init_data"}, status=400)
    telegram_id = user_data.get("id")
    if not telegram_id:
        logger.warning("tg_webapp_auth: no_user (user_data without id)")
        return JsonResponse({"ok": False, "error": "no_user"}, status=400)

    # Majburiy kanallarga obuna bo'lgan-bo'lmaganini tekshirish
    if not required_channels_ok_for_telegram_id(telegram_id):
        logger.warning("tg_webapp_auth: subscription_required telegram_id=%s", telegram_id)
        return JsonResponse({"ok": False, "error": "subscription_required"}, status=403)

    # Rate limit: bir foydalanuvchi uchun tez-tez auth bo'lishiga yo'l qo'ymaslik
    if not check_rate_limit(f"tg_webapp_auth_{telegram_id}"):
        logger.warning("tg_webapp_auth: rate_limited telegram_id=%s", telegram_id)
        return JsonResponse(
            {"ok": False, "error": "rate_limited"},
            status=429,
        )
    user = get_or_create_user_by_telegram(
        telegram_id=telegram_id,
        first_name=user_data.get("first_name", ""),
    )
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    logger.info("tg_webapp_auth: ok telegram_id=%s user_id=%s", telegram_id, user.pk)
    return JsonResponse({"ok": True, "redirect": "/"})
