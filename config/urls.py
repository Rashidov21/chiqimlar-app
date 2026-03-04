"""Chiqimlar - Asosiy URL konfiguratsiyasi."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("expenses.urls")),
    path("", include("accounts.urls")),
    path("", include("categories.urls")),
    path("", include("analytics.urls")),
    path("", include("notifications.urls")),
    path("telegram/", include("telegram_bot.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
