from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, VerificationCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "telegram_id", "email", "monthly_budget", "is_active"]
    list_filter = ["is_staff", "is_active"]
    search_fields = ["username", "first_name", "telegram_id"]
    ordering = ["-date_joined"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Telegram", {"fields": ("telegram_id", "phone")}),
        ("Byudjet", {"fields": ("monthly_budget",)}),
        ("Bildirishnomalar", {"fields": ("telegram_notifications", "daily_reminder", "weekly_summary", "limit_warning")}),
    )


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "telegram_id", "user", "is_used", "created_at", "expires_at"]
    list_filter = ["is_used"]
    search_fields = ["code", "telegram_id"]
    readonly_fields = ["created_at"]
