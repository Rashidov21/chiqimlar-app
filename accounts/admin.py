from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from telegram_bot.services import clear_subscription_cache_for_user
from .models import User, VerificationCode, DonationMethod, Donation


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "telegram_id", "email", "monthly_budget", "is_supporter", "is_active"]
    list_filter = ["is_staff", "is_active", "is_supporter"]
    search_fields = ["username", "first_name", "telegram_id"]
    ordering = ["-date_joined"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Telegram", {"fields": ("telegram_id", "phone")}),
        ("Byudjet", {"fields": ("monthly_budget",)}),
        ("Bildirishnomalar", {"fields": ("telegram_notifications", "daily_reminder", "weekly_summary", "limit_warning")}),
        ("Donater", {"fields": ("is_supporter",)}),
    )
    actions = ["clear_subscription_cache"]

    def clear_subscription_cache(self, request, queryset):
        cleared = 0
        for user in queryset:
            if user.telegram_id:
                clear_subscription_cache_for_user(user.telegram_id)
                cleared += 1
        if cleared:
            self.message_user(request, f"{cleared} ta foydalanuvchi uchun kanal obunasi cache'i tozalandi.")
        else:
            self.message_user(request, "Tanlangan foydalanuvchilarda telegram_id topilmadi.")

    clear_subscription_cache.short_description = "Tanlangan foydalanuvchilar uchun kanal obunasi cache'ini tozalash"


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "telegram_id", "user", "is_used", "created_at", "expires_at"]
    list_filter = ["is_used"]
    search_fields = ["code", "telegram_id"]
    readonly_fields = ["created_at"]


@admin.register(DonationMethod)
class DonationMethodAdmin(admin.ModelAdmin):
    list_display = ["title", "is_active", "sort_order"]
    list_filter = ["is_active"]
    search_fields = ["title"]
    ordering = ["sort_order", "id"]


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ["user", "amount", "method", "confirmed", "short_note", "created_at"]
    list_filter = ["confirmed", "method"]
    search_fields = ["user__username", "user__telegram_id"]
    readonly_fields = ["created_at"]

    actions = ["mark_as_confirmed"]

    def mark_as_confirmed(self, request, queryset):
        updated = 0
        for donation in queryset:
            if not donation.confirmed:
                donation.confirmed = True
                donation.save(update_fields=["confirmed"])
                if donation.user and not donation.user.is_supporter:
                    donation.user.is_supporter = True
                    donation.user.save(update_fields=["is_supporter"])
                updated += 1
        self.message_user(request, f"{updated} ta donat tasdiqlandi va foydalanuvchilar donater sifatida belgilandi.")

    mark_as_confirmed.short_description = "Tanlangan donatlarni tasdiqlash va foydalanuvchilarni donater qilish"

    def short_note(self, obj):
        text = (obj.note or "").strip()
        if len(text) > 40:
            return text[:39] + "…"
        return text or "-"

    short_note.short_description = "Izoh"