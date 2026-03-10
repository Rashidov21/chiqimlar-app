"""
Xarajatlar - Chiqimlar, jamg'arma maqsadlari va byudjet.
"""
from django.db import models
from django.conf import settings


class Expense(models.Model):
    """Yagona xarajat yozuvi."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expenses",
    )
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    note = models.CharField(max_length=255, blank=True)
    date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Xarajat"
        verbose_name_plural = "Xarajatlar"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.amount} — {self.date}"


class SavingGoal(models.Model):
    """Jamg'arma maqsadi (target summa va progress)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saving_goals",
    )
    name = models.CharField(max_length=120)
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        help_text="Yig'moqchi bo'lgan jami summa (so'm)",
    )
    current_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        help_text="Hozircha jamg'arilgan summa (so'm)",
    )
    start_date = models.DateField()
    target_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Jamg'arma maqsadi"
        verbose_name_plural = "Jamg'arma maqsadlari"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_active"])]

    def __str__(self):
        return f"{self.name} ({self.user})"

    @property
    def progress_percent(self):
        if not self.target_amount or self.target_amount <= 0:
            return 0
        return min(int(self.current_amount / self.target_amount * 100), 100)

    @property
    def remaining_amount(self):
        return max(self.target_amount - self.current_amount, 0)


class RecurringExpense(models.Model):
    """Qayta takrorlanuvchi chiqimlar (ijara, internet va h.k.)."""

    class Interval(models.TextChoices):
        MONTHLY = "monthly", "Oylik"
        WEEKLY = "weekly", "Haftalik"
        YEARLY = "yearly", "Yillik"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recurring_expenses",
    )
    name = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recurring_expenses",
    )
    interval = models.CharField(
        max_length=16,
        choices=Interval.choices,
        default=Interval.MONTHLY,
    )
    next_payment_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Qayta takrorlanuvchi chiqim"
        verbose_name_plural = "Qayta takrorlanuvchi chiqimlar"
        ordering = ["next_payment_date", "name"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["user", "next_payment_date"]),
        ]

    def __str__(self):
        return f"{self.name} — {self.amount}"


class Debt(models.Model):
    """Qarz va qarzdorliklar."""

    class Kind(models.TextChoices):
        TAKEN = "taken", "Olingan qarz"
        GIVEN = "given", "Berilgan qarz"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="debts",
    )
    kind = models.CharField(
        max_length=16,
        choices=Kind.choices,
        default=Kind.TAKEN,
    )
    counterparty = models.CharField(
        max_length=120,
        help_text="Kimdan qarz oldingiz yoki kimga berdingiz",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    date = models.DateField(help_text="Qarz olingan/berilgan sana")
    due_date = models.DateField(null=True, blank=True, help_text="Qaytarish muddati (ixtiyoriy)")
    note = models.CharField(max_length=255, blank=True)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Qarz"
        verbose_name_plural = "Qarz va qarzdorliklar"
        ordering = ["is_closed", "due_date", "-created_at"]
        indexes = [
            models.Index(fields=["user", "is_closed"]),
            models.Index(fields=["user", "kind", "is_closed"]),
        ]

    def __str__(self):
        direction = "Oldim" if self.kind == self.Kind.TAKEN else "Berdim"
        return f"{direction} — {self.counterparty} — {self.amount}"
