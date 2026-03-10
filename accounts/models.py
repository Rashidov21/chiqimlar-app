"""
Hisoblar - Foydalanuvchi, moliyaviy profil va tasdiqlash kodi modellari.
"""
import secrets
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Telegram bilan bog'langan foydalanuvchi."""

    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    monthly_budget = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        help_text="Oylik byudjet (so'm)",
    )
    telegram_notifications = models.BooleanField(default=True)
    daily_reminder = models.BooleanField(default=True)
    weekly_summary = models.BooleanField(default=True)
    limit_warning = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return self.get_display_name()

    def get_display_name(self):
        if self.get_full_name():
            return self.get_full_name().strip()
        if self.username:
            return self.username
        return f"Foydalanuvchi #{self.pk}"


class FinanceProfile(models.Model):
    """Foydalanuvchining moliyaviy profili va onboarding holati."""

    class PrimaryGoal(models.TextChoices):
        GENERAL_SAVING = "saving", "Jamg'arma oshirish"
        DEBT_REDUCTION = "debt", "Qarzdan chiqish"
        SPENDING_CONTROL = "spending_control", "Xarajatlarni nazorat qilish"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="finance_profile",
    )
    primary_goal = models.CharField(
        max_length=32,
        choices=PrimaryGoal.choices,
        default=PrimaryGoal.GENERAL_SAVING,
    )
    preferred_categories = models.ManyToManyField(
        "categories.Category",
        blank=True,
        related_name="preferred_by_users",
    )
    preferred_currency = models.CharField(
        max_length=8,
        default="UZS",
        help_text="Asosiy valyuta (masalan: UZS, USD)",
    )
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Moliyaviy profil"
        verbose_name_plural = "Moliyaviy profillar"

    def __str__(self):
        return f"Moliyaviy profil — {self.user.get_display_name()}"


class VerificationCode(models.Model):
    """Telegram orqali kirish uchun tasdiqlash kodi."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="verification_codes",
    )
    telegram_id = models.BigIntegerField(db_index=True)
    code = models.CharField(max_length=8, db_index=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "Tasdiqlash kodi"
        verbose_name_plural = "Tasdiqlash kodlari"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code", "is_used"]),
            models.Index(fields=["telegram_id", "expires_at"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.telegram_id}"

    @classmethod
    def generate(cls, telegram_id: int, user=None):
        from django.utils import timezone
        from datetime import timedelta
        from django.conf import settings

        code = secrets.token_hex(4).upper()[:6]
        expire_minutes = getattr(settings, "VERIFICATION_CODE_EXPIRE_MINUTES", 10)
        expires_at = timezone.now() + timedelta(minutes=expire_minutes)
        return cls.objects.create(
            user=user,
            telegram_id=telegram_id,
            code=code,
            expires_at=expires_at,
        )

    def is_valid(self):
        from django.utils import timezone

        return not self.is_used and timezone.now() < self.expires_at
