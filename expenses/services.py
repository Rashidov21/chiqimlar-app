"""
Xarajatlar - Dashboard va byudjet hisoblashlari.
Barcha dashboard ma'lumotlari bitta get_dashboard_context orqali yig'iladi.
"""
from datetime import date as date_type
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from accounts.models import User


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
    """Oy bo'yicha turkumlar bo'yicha yig'indi (bitta group-by query bilan)."""
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
    from .models import Expense

    # category_id -> summa
    raw = (
        Expense.objects.filter(
            user=user,
            date__gte=month_start,
            date__lte=month_end,
            category_id__isnull=False,
        )
        .values("category_id")
        .annotate(total=Sum("amount"))
    )
    totals_by_cat = {row["category_id"]: row["total"] or Decimal("0") for row in raw}

    breakdown = []
    for cat in Category.objects.filter(user=user).order_by("order", "name"):
        total = totals_by_cat.get(cat.id)
        if total and total > 0:
            breakdown.append({"category": cat, "total": total})
    return breakdown


def get_daily_summary(user, date=None):
    """
    Bugungi (yoki berilgan sana uchun) qisqa eslatma:
    - sarflangan summa
    - oy byudjeti asosida taxminiy kunlik limit
    - qolgan / ortiqcha sarf.
    """
    from datetime import date as _date

    today = timezone.now().date()
    current_date = date or today
    if not isinstance(current_date, _date):
        current_date = today

    totals = get_monthly_totals(user, year=current_date.year, month=current_date.month)
    spent_today = (
        user.expenses.filter(date=current_date).aggregate(s=Sum("amount"))["s"]
        or Decimal("0")
    )
    budget = totals["budget"] or Decimal("0")
    month_remaining = totals["remaining"] or Decimal("0")
    days_left = max((totals["month_end"] - current_date).days + 1, 1)
    recommended_daily = (
        month_remaining / days_left if budget > 0 and month_remaining > 0 else Decimal("0")
    )
    remaining_for_today = recommended_daily - spent_today

    return {
        "date": current_date,
        "spent_today": spent_today,
        "budget": budget,
        "month_remaining": month_remaining,
        "recommended_daily": recommended_daily,
        "remaining_for_today": remaining_for_today,
        "is_over_for_today": remaining_for_today < 0,
    }


MONTH_NAMES = [
    "",
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
]


def _next_payment_date(current_date, interval: str):
    """Interval bo'yicha keyingi to'lov sanasini hisoblaydi (faqat datetime/calendar)."""
    from calendar import monthrange
    from datetime import date as date_cls

    if interval == "weekly":
        return current_date + timezone.timedelta(days=7)
    if interval == "yearly":
        try:
            return current_date.replace(year=current_date.year + 1)
        except ValueError:
            return current_date.replace(year=current_date.year + 1, day=28)
    # monthly va default
    y, m = current_date.year, current_date.month
    m += 1
    if m > 12:
        m -= 12
        y += 1
    _, last = monthrange(y, m)
    day = min(current_date.day, last)
    return date_cls(y, m, day)


def advance_next_payment(recurring, create_expense: bool = False):
    """
    Qayta takrorlanuvchi chiqim uchun keyingi to'lov sanasini hisoblaydi va yangilaydi.
    Ixtiyoriy: to'lov qilingan sana uchun Expense yozuvi yaratadi.
    """
    from .models import RecurringExpense, Expense

    if not isinstance(recurring, RecurringExpense):
        return
    pay_date = recurring.next_payment_date
    next_date = _next_payment_date(pay_date, recurring.interval)
    recurring.next_payment_date = next_date
    recurring.save(update_fields=["next_payment_date", "updated_at"])

    if create_expense:
        Expense.objects.create(
            user=recurring.user,
            category=recurring.category,
            amount=recurring.amount,
            note=f"Qayta chiqim: {recurring.name}",
            date=pay_date,
        )


def get_dashboard_context(user: User, selected_date: date_type | None = None) -> dict:
    """
    Dashboard uchun barcha ma'lumotlarni yig'adi (insights va achievements dan tashqari).
    View bu context'ga analytics'dan insights va achievements qo'shadi.
    """
    from .models import Expense, RecurringExpense, Debt

    today = timezone.now().date()
    if selected_date is None:
        selected_date = today

    data = get_monthly_totals(user, year=selected_date.year, month=selected_date.month)
    breakdown = get_category_breakdown(user, year=selected_date.year, month=selected_date.month)
    daily_summary = get_daily_summary(user)
    month_start = data["month_start"]
    month_end = data["month_end"]
    days_count = max((month_end - month_start).days + 1, 1)
    avg_daily = (
        data["total_spent"] / days_count if data["total_spent"] > 0 else Decimal("0")
    )
    top_categories = breakdown[:3]
    month_display = f"{MONTH_NAMES[data['month']]} {data['year']}"
    selected_date_display = (
        f"{selected_date.day} {MONTH_NAMES[selected_date.month].lower()} {selected_date.year}"
    )

    upcoming_recurring = (
        RecurringExpense.objects.filter(
            user=user,
            is_active=True,
            next_payment_date__gte=today,
        )
        .order_by("next_payment_date")[:5]
    )
    open_debts = Debt.objects.filter(user=user, is_closed=False)
    taken_total = sum(d.amount for d in open_debts if d.kind == Debt.Kind.TAKEN)
    given_total = sum(d.amount for d in open_debts if d.kind == Debt.Kind.GIVEN)
    net_debt = taken_total - given_total
    net_debt_abs = abs(net_debt)

    recent = (
        Expense.objects.filter(user=user, date__gte=month_start, date__lte=month_end)
        .select_related("category")
        .order_by("-date", "-created_at")[:10]
    )

    return {
        "totals": data,
        "month_display": month_display,
        "selected_date_display": selected_date_display,
        "selected_date_iso": selected_date.isoformat(),
        "breakdown": breakdown,
        "recent": recent,
        "avg_daily": avg_daily,
        "top_categories": top_categories,
        "daily_summary": daily_summary,
        "upcoming_recurring": upcoming_recurring,
        "net_debt": net_debt,
        "net_debt_abs": net_debt_abs,
        "taken_debt_total": taken_total,
        "given_debt_total": given_total,
    }
