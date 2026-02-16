"""
Telegram webhook - xavfsiz qabul qilish.
"""
import json
import logging
from django.http import HttpResponse, HttpRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

logger = logging.getLogger(__name__)


def _verify_telegram_secret(request: HttpRequest) -> bool:
    """Webhook so'rovida secret tekshirish (header yoki query)."""
    secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "")
    if not secret:
        return True
    header = request.headers.get("X-Telegram-Webhook-Secret") or request.headers.get("X-Webhook-Secret")
    if header == secret:
        return True
    return request.GET.get("secret") == secret


@require_POST
@csrf_exempt
def webhook(request: HttpRequest):
    """
    Telegram webhook endpoint.
    Bot token orqali Telegram xavfsizlikni o'zi tekshiradi; qo'shimcha secret ixtiyoriy.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        return HttpResponse("Bot sozlanmagan", status=503)
    if not _verify_telegram_secret(request):
        return HttpResponse("Forbidden", status=403)
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Bad request", status=400)
    try:
        from .handlers import process_update
        process_update(body)
    except Exception as e:
        logger.exception("Webhook error: %s", e)
    return HttpResponse("OK")
