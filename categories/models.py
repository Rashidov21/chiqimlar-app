"""
Turkumlar - Xarajat kategoriyalari va kategoriya bo'yicha byudjetlar.
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


class CategoryBudget(models.Model):
    """Konkret oy uchun turkum bo'yicha byudjet limiti."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="category_budgets",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="budgets",
    )
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        help_text="Ushbu oy uchun turkum byudjeti (so'm)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Turkum byudjeti"
        verbose_name_plural = "Turkum bo'yicha byudjetlar"
        unique_together = [["user", "category", "year", "month"]]
        indexes = [
            models.Index(fields=["user", "year", "month"]),
            models.Index(fields=["category", "year", "month"]),
        ]

    def __str__(self):
        return f"{self.category.name} — {self.year}-{self.month:02d}"
