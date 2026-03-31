"""
Chiqimlar - Statik sahifalar: 404, 500, Maxfiylik, Yordam, Health check.
"""
from django.http import JsonResponse
from django.shortcuts import render
from django.views.defaults import page_not_found, server_error
from django.conf import settings


def custom_404(request, exception=None):
    """Maxsus 404 sahifa."""
    return render(request, "404.html", status=404)


def custom_500(request):
    """Maxsus 500 sahifa."""
    return render(request, "500.html", status=500)


def privacy_view(request):
    """Maxfiylik siyosati sahifasi."""
    return render(request, "pages/privacy.html")


def help_view(request):
    """Yordam sahifasi."""
    return render(request, "pages/help.html")


def donater_landing_view(request):
    """Public landing page: Donater premium qiymatini sotuvchi sahifa."""
    bot_username = (getattr(settings, "TELEGRAM_BOT_USERNAME", "") or "").strip().lstrip("@")
    bot_link = f"https://t.me/{bot_username}" if bot_username else ""
    webapp_login_url = (getattr(settings, "TELEGRAM_WEBAPP_URL", "") or "").strip()
    return render(
        request,
        "pages/donater.html",
        {
            "bot_link": bot_link,
            "webapp_login_url": webapp_login_url,
            "bot_username": bot_username,
        },
    )


def health_view(request):
    """Health check — monitoring va load balancer uchun (DB tekshiruvi)."""
    from django.db import connection
    try:
        connection.ensure_connection()
        return JsonResponse({"status": "ok", "db": "connected"})
    except Exception:
        return JsonResponse({"status": "error", "db": "disconnected"}, status=503)
