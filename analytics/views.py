"""
Umumiy statistika - oy/kun, grafiklar, tushunchalar.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Sum

from .services import (
    get_insights_for_user,
    get_daily_totals,
    get_category_totals_for_period,
    get_monthly_trend,
)
from expenses.services import get_monthly_totals, get_category_breakdown
from expenses.models import Expense

MONTH_NAMES = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
]
MIN_YEAR = 2000
MAX_YEAR = 2100


@login_required
def statistics_view(request):
    """Umumiy statistika - oy tanlash, kunlik/oylik, grafiklar."""
    today = timezone.now().date()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
    except (ValueError, TypeError):
        year, month = today.year, today.month
    if not (1 <= month <= 12):
        month = today.month
    if not (MIN_YEAR <= year <= MAX_YEAR):
        year = today.year
    view_type = request.GET.get("view", "month")
    if view_type not in ("month", "day"):
        view_type = "month"

    totals = get_monthly_totals(request.user, year=year, month=month)
    breakdown = get_category_breakdown(request.user, year=year, month=month)
    insights = get_insights_for_user(request.user, year=year, month=month, limit=5)
    daily = get_daily_totals(request.user, year, month)
    month_start = today.replace(year=year, month=month, day=1)
    if month == 12:
        month_end = month_start.replace(year=year + 1, month=1, day=1) - timezone.timedelta(days=1)
    else:
        month_end = month_start.replace(month=month + 1, day=1) - timezone.timedelta(days=1)
    if year == today.year and month == today.month:
        month_end = today
    category_chart = get_category_totals_for_period(request.user, month_start, month_end)
    trend = get_monthly_trend(request.user, 6)
    trend_12 = get_monthly_trend(request.user, 12) if getattr(request.user, "is_supporter", False) else []

    # Qo'shimcha agregatlar: kunlik o'rtacha va o'tgan oyga nisbatan o'zgarish
    this_total = totals["total_spent"]
    month_days = max((month_end - month_start).days + 1, 1)
    avg_daily = float(this_total / month_days) if this_total > 0 else 0.0

    prev_change_pct = None
    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1
    prev_totals = get_monthly_totals(request.user, year=prev_year, month=prev_month)
    prev_total = prev_totals["total_spent"]
    if prev_total > 0:
        prev_change_pct = float((this_total - prev_total) / prev_total * 100)

    daily_max = max((d["total"] for d in daily), default=0)
    if daily_max <= 0:
        daily_max = 1
    trend_max = max((t["total"] for t in trend), default=0)
    if trend_max <= 0:
        trend_max = 1
    trend_12_max = max((t["total"] for t in trend_12), default=0)
    if trend_12_max <= 0:
        trend_12_max = 1

    years = list(range(max(MIN_YEAR, year - 2), min(MAX_YEAR, year + 2) + 1))
    months = list(range(1, 13))
    month_choices = list(zip(months, MONTH_NAMES))
    selected_month_name = MONTH_NAMES[month - 1] if 1 <= month <= 12 else ""

    # Kunlar view uchun qo'shimcha filtrlar
    selected_day = None
    day_choices = []
    day_total = None
    day_breakdown = []
    selected_day_label = ""
    if view_type == "day":
        try:
            selected_day = int(request.GET.get("day", today.day if (year == today.year and month == today.month) else 1))
        except (ValueError, TypeError):
            selected_day = today.day if (year == today.year and month == today.month) else 1
        selected_day = min(max(selected_day, 1), month_end.day)
        day_choices = list(range(1, month_end.day + 1))
        selected_date = month_start.replace(day=selected_day)
        selected_day_label = f"{selected_day} {selected_month_name.lower()} {year}"
        day_qs = Expense.objects.filter(user=request.user, date=selected_date)
        day_total = day_qs.aggregate(s=Sum("amount"))["s"] or 0
        day_breakdown = (
            day_qs.values("category__emoji", "category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

    # Oy bo'yicha oldingi/keyingi navigatsiya
    if month == 1:
        prev_month_year, prev_month = year - 1, 12
    else:
        prev_month_year, prev_month = year, month - 1
    if month == 12:
        next_month_year, next_month = year + 1, 1
    else:
        next_month_year, next_month = year, month + 1

    user = request.user
    is_supporter = getattr(user, "is_supporter", False)
    can_see_advanced = is_supporter

    return render(
        request,
        "analytics/statistics.html",
        {
            "totals": totals,
            "breakdown": breakdown,
            "insights": insights,
            "daily": daily,
            "category_chart": category_chart,
            "trend": trend,
            "view_type": view_type,
            "selected_year": year,
            "selected_month": month,
            "selected_month_name": selected_month_name,
            "daily_max": daily_max,
            "trend_max": trend_max,
            "years": years,
            "months": months,
            "month_choices": month_choices,
            "avg_daily": avg_daily,
            "prev_change_pct": prev_change_pct,
            "selected_day": selected_day,
            "day_choices": day_choices,
            "day_total": day_total,
            "day_breakdown": day_breakdown,
            "selected_day_label": selected_day_label,
            "prev_month_year": prev_month_year,
            "prev_month": prev_month,
            "next_month_year": next_month_year,
            "next_month": next_month,
            "is_supporter": is_supporter,
            "can_see_advanced_statistics": can_see_advanced,
            "trend_12": trend_12,
            "trend_12_max": trend_12_max,
        },
    )


@login_required
def chart_data_daily(request):
    """Kunlik grafik ma'lumotlari (API)."""
    today = timezone.now()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
    except (ValueError, TypeError):
        year, month = today.year, today.month
    if not (1 <= month <= 12):
        month = today.month
    if not (MIN_YEAR <= year <= MAX_YEAR):
        year = today.year
    raw = get_daily_totals(request.user, year, month)
    data = [
        {"date": d["date"].isoformat(), "total": float(d["total"])}
        for d in raw
    ]
    return JsonResponse({"data": data})


@login_required
def chart_data_categories(request):
    """Kategoriya grafik ma'lumotlari."""
    from datetime import date
    from calendar import monthrange

    today = timezone.now().date()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
    except (ValueError, TypeError):
        year, month = today.year, today.month
    if not (1 <= month <= 12):
        month = today.month
    if not (MIN_YEAR <= year <= MAX_YEAR):
        year = today.year
    start = date(year, month, 1)
    _, last_day = monthrange(year, month)
    # Joriy oy bo'lsa bugungacha, o'tgan oylar uchun oy oxirigacha
    if year == today.year and month == today.month:
        end = today
    else:
        end = date(year, month, last_day)
    data = get_category_totals_for_period(request.user, start, end)
    return JsonResponse({"data": data})
