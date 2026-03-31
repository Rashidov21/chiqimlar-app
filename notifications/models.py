from django.conf import settings
from django.db import models
from django.utils import timezone


class CampaignMessageTemplate(models.Model):
    class Segment(models.TextChoices):
        NEW = "new", "Yangi user (0-3 kun)"
        ACTIVE = "active", "Faol non-donater"
        INACTIVE = "inactive", "Noactive non-donater"

    key = models.CharField(max_length=64, unique=True)
    segment = models.CharField(max_length=16, choices=Segment.choices, db_index=True)
    topic = models.CharField(max_length=24, default="general", db_index=True)
    text = models.TextField()
    cta_url = models.CharField(max_length=255, blank=True, help_text="Masalan: /expenses/settings/")
    is_active = models.BooleanField(default=True, db_index=True)
    weight = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["segment", "-weight", "key"]

    def __str__(self):
        return f"{self.key} ({self.segment})"


class CampaignDeliveryLog(models.Model):
    class Status(models.TextChoices):
        SENT = "sent", "Yuborildi"
        FAILED = "failed", "Xatolik"
        SKIPPED = "skipped", "Qoidaga tushib o'tkazib yuborildi"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="campaign_logs"
    )
    template = models.ForeignKey(
        CampaignMessageTemplate, null=True, blank=True, on_delete=models.SET_NULL, related_name="delivery_logs"
    )
    status = models.CharField(max_length=16, choices=Status.choices, db_index=True)
    skip_reason = models.CharField(max_length=64, blank=True)
    message_text = models.TextField(blank=True)
    sent_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["user", "sent_at"]),
            models.Index(fields=["status", "sent_at"]),
        ]

    def __str__(self):
        return f"{self.user_id} {self.status} {self.sent_at:%Y-%m-%d %H:%M}"


class UserCampaignState(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="campaign_state"
    )
    promo_opt_out = models.BooleanField(default=False)
    weekly_window_start = models.DateField(default=timezone.now, db_index=True)
    weekly_send_count = models.PositiveSmallIntegerField(default=0)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    next_send_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_topic = models.CharField(max_length=24, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Campaign state"
        verbose_name_plural = "Campaign states"

    def __str__(self):
        return f"campaign-state:{self.user_id}"
