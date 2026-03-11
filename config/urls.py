"""Chiqimlar - Asosiy URL konfiguratsiyasi."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from config.views import privacy_view, help_view, health_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_view),
    path("privacy/", privacy_view),
    path("yordam/", help_view),
    path("", include("expenses.urls")),
    path("", include("accounts.urls")),
    path("", include("categories.urls")),
    path("", include("analytics.urls")),
    path("", include("notifications.urls")),
    path("telegram/", include("telegram_bot.urls")),
    path("api/v1/", include("api.urls")),
]

handler404 = "config.views.custom_404"
handler500 = "config.views.custom_500"

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
