from django.db import models
from django.conf import settings


class Achievement(models.Model):
    """Gamifikatsiya uchun umumiy yutuqlar ro'yxati."""

    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Yutuq"
        verbose_name_plural = "Yutuqlar"

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """Foydalanuvchi olgan yutuqlar."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_achievements",
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name="user_achievements",
    )
    obtained_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foydalanuvchi yutug'i"
        verbose_name_plural = "Foydalanuvchi yutuqlari"
        unique_together = [["user", "achievement"]]
        ordering = ["-obtained_at"]

    def __str__(self):
        return f"{self.user} — {self.achievement}"
