"""
Rate limiting: abuse va DoS oldini olish.
Cache asosida, identifier (user_id yoki IP) bo'yicha.
"""
import time
import logging
from functools import wraps
from django.core.cache import cache
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages

logger = logging.getLogger(__name__)

# Default: 30 so'rov / 60 soniya per user
RATE_LIMIT_WINDOW = int(getattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60))
RATE_LIMIT_MAX_REQUESTS = int(getattr(settings, "RATE_LIMIT_MAX_REQUESTS", 30))
RATE_LIMIT_KEY_PREFIX = "rl:"


def _rate_limit_key(identifier: str, action: str) -> str:
    return f"{RATE_LIMIT_KEY_PREFIX}{action}:{identifier}"


def check_rate_limit(identifier: str, action: str, window: int = RATE_LIMIT_WINDOW, max_requests: int = RATE_LIMIT_MAX_REQUESTS) -> bool:
    """
    True = limit oshmagan, ruxsat beramiz.
    False = limit oshgan, rad etamiz.
    """
    key = _rate_limit_key(identifier, action)
    data = cache.get(key) or {"count": 0, "start": time.time()}
    now = time.time()
    if now - data["start"] > window:
        data = {"count": 0, "start": now}
    data["count"] += 1
    cache.set(key, data, timeout=window + 10)
    return data["count"] <= max_requests


def rate_limit_action(action: str, window: int = RATE_LIMIT_WINDOW, max_requests: int = RATE_LIMIT_MAX_REQUESTS):
    """
    View decorator: login qilingan user uchun rate limit.
    Limit oshganda: HTML request da redirect + message, AJAX da 429.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            identifier = str(request.user.pk)
            if not check_rate_limit(identifier, action, window=window, max_requests=max_requests):
                logger.warning("rate_limit exceeded user_id=%s action=%s", request.user.pk, action)
                if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accepts("application/json"):
                    return JsonResponse(
                        {"ok": False, "error": "rate_limited", "detail": "Juda ko'p so'rov. Biroz kutib qaytadan urinib ko'ring."},
                        status=429,
                    )
                messages.error(
                    request,
                    "Juda ko'p amal bajarildi. Bir daqiqadan keyin qaytadan urinib ko'ring.",
                )
                return redirect("expenses:dashboard")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
