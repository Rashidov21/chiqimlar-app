from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from telegram_bot.services import clear_subscription_cache_for_user
from .models import User, VerificationCode, DonationMethod, Donation
from notifications.services import send_telegram_message


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
    list_display = ["user", "amount", "method", "status", "confirmed", "short_note", "created_at"]
    list_filter = ["status", "confirmed", "method"]
    search_fields = ["user__username", "user__telegram_id"]
    readonly_fields = ["created_at"]

    actions = ["mark_as_confirmed", "mark_as_rejected", "mark_as_pending"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by("status", "-created_at")

    def mark_as_confirmed(self, request, queryset):
        updated = 0
        for donation in queryset:
            if donation.status != Donation.Status.APPROVED:
                donation.status = Donation.Status.APPROVED
                donation.rejection_reason = ""
                donation.save(update_fields=["status", "rejection_reason", "confirmed"])
                if donation.user and not donation.user.is_supporter:
                    donation.user.is_supporter = True
                    donation.user.save(update_fields=["is_supporter"])
                if donation.user and donation.user.telegram_id:
                    send_telegram_message(
                        donation.user.telegram_id,
                        "🎉 Donatingiz tasdiqlandi! Sizga Donater statusi berildi. Rahmat!",
                    )
                updated += 1
        self.message_user(request, f"{updated} ta donat tasdiqlandi va foydalanuvchilar donater sifatida belgilandi.")

    mark_as_confirmed.short_description = "Tanlangan donatlarni tasdiqlash va foydalanuvchilarni donater qilish"

    def mark_as_rejected(self, request, queryset):
        updated = 0
        for donation in queryset:
            if donation.status != Donation.Status.REJECTED:
                donation.status = Donation.Status.REJECTED
                if not donation.rejection_reason:
                    donation.rejection_reason = "Chek bo'yicha ma'lumot aniqlashtirish talab qilindi."
                donation.save(update_fields=["status", "rejection_reason", "confirmed"])
                if donation.user and donation.user.telegram_id:
                    send_telegram_message(
                        donation.user.telegram_id,
                        "❌ Donat tekshiruv natijasi: hozircha tasdiqlanmadi. Iltimos, chek screenshotini aniqroq ma'lumot bilan qayta yuboring.",
                    )
                updated += 1
        self.message_user(request, f"{updated} ta donat rad etildi.")

    mark_as_rejected.short_description = "Tanlangan donatlarni rad etish (qayta screenshot so'rash)"

    def mark_as_pending(self, request, queryset):
        updated = 0
        for donation in queryset:
            if donation.status != Donation.Status.PENDING:
                donation.status = Donation.Status.PENDING
                donation.rejection_reason = ""
                donation.save(update_fields=["status", "rejection_reason", "confirmed"])
                updated += 1
        self.message_user(request, f"{updated} ta donat qayta tekshiruvga yuborildi.")

    mark_as_pending.short_description = "Tanlangan donatlarni qayta tekshiruvga o'tkazish"

    def short_note(self, obj):
        text = (obj.note or "").strip()
        if len(text) > 40:
            return text[:39] + "…"
        return text or "-"

    short_note.short_description = "Izoh"