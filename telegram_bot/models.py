from django.db import models


class RequiredChannel(models.Model):
    """
    Foydalanuvchi ilovadan foydalanishi uchun obuna bo'lishi kerak bo'lgan Telegram kanallar.
    """

    name = models.CharField(max_length=120, help_text="Kanal nomi (admin uchun).")
    username = models.CharField(
        max_length=64,
        help_text="@kanal_username (masalan, @chiqimlar_kanal) yoki short name.",
    )
    channel_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Ixtiyoriy: aniq channel_id (agar ma'lum bo'lsa).",
    )
    is_active = models.BooleanField(default=True)
    is_mandatory = models.BooleanField(
        default=True,
        help_text="True bo'lsa — ushbu kanalda bo'lmagan user ilovaga kira olmaydi.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Majburiy kanal"
        verbose_name_plural = "Majburiy kanallar"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

