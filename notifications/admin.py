from django.contrib import admin

from .models import CampaignMessageTemplate, CampaignDeliveryLog, UserCampaignState


@admin.register(CampaignMessageTemplate)
class CampaignMessageTemplateAdmin(admin.ModelAdmin):
    list_display = ["key", "segment", "topic", "is_active", "weight", "updated_at"]
    list_filter = ["segment", "topic", "is_active"]
    search_fields = ["key", "text"]
    ordering = ["segment", "key"]


@admin.register(CampaignDeliveryLog)
class CampaignDeliveryLogAdmin(admin.ModelAdmin):
    list_display = ["user", "template", "status", "skip_reason", "sent_at"]
    list_filter = ["status", "template__segment", "template__topic"]
    search_fields = ["user__username", "user__telegram_id", "message_text", "skip_reason"]
    readonly_fields = ["created_at", "sent_at", "message_text"]
    ordering = ["-sent_at"]


@admin.register(UserCampaignState)
class UserCampaignStateAdmin(admin.ModelAdmin):
    list_display = ["user", "promo_opt_out", "weekly_send_count", "weekly_window_start", "next_send_at", "last_topic"]
    list_filter = ["promo_opt_out"]
    search_fields = ["user__username", "user__telegram_id"]
