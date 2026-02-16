"""
Xarajatlar - Dashboard va byudjet hisoblashlari.
"""
from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone


def get_monthly_totals(user, year=None, month=None):
    """Berilgan oy uchun jami xarajat va byudjet."""
    today = timezone.now().date()
    year = year or today.year
    month = month or today.month
    month_start = today.replace(year=year, month=month, day=1)
    if month == 12:
        month_end = month_start.replace(year=year + 1, month=1, day=1) - timezone.timedelta(days=1)
    else:
        month_end = month_start.replace(month=month + 1, day=1) - timezone.timedelta(days=1)
    if month == today.month and year == today.year:
        month_end = today
    total = (
        user.expenses.filter(date__gte=month_start, date__lte=month_end)
        .aggregate(s=Sum("amount"))["s"]
        or Decimal("0")
    )
    budget = user.monthly_budget or Decimal("0")
    remaining = budget - total
    return {
        "total_spent": total,
        "budget": budget,
        "remaining": remaining,
        "month_start": month_start,
        "month_end": month_end,
        "year": year,
        "month": month,
    }


def get_category_breakdown(user, year=None, month=None):
    """Oy bo'yicha turkumlar bo'yicha yig'indi."""
    today = timezone.now().date()
    year = year or today.year
    month = month or today.month
    month_start = today.replace(year=year, month=month, day=1)
    if month == 12:
        month_end = month_start.replace(year=year + 1, month=1, day=1) - timezone.timedelta(days=1)
    else:
        month_end = month_start.replace(month=month + 1, day=1) - timezone.timedelta(days=1)
    if month == today.month and year == today.year:
        month_end = today
    from categories.models import Category
    breakdown = []
    for cat in Category.objects.filter(user=user).order_by("order", "name"):
        s = (
            cat.expenses.filter(date__gte=month_start, date__lte=month_end)
            .aggregate(s=Sum("amount"))["s"]
            or Decimal("0")
        )
        if s > 0:
            breakdown.append({"category": cat, "total": s})
    return breakdown
