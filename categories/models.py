"""
Turkumlar - Xarajat kategoriyalari.
"""
from django.db import models
from django.conf import settings


class Category(models.Model):
    """Xarajat turkumi (emoji + nom)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=10, default="📁")
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Turkum"
        verbose_name_plural = "Turkumlar"
        ordering = ["order", "name"]
        unique_together = [["user", "name"]]
        indexes = [models.Index(fields=["user"])]

    def __str__(self):
        return f"{self.emoji} {self.name}"
