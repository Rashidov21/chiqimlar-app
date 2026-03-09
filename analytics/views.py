"""
Umumiy statistika - oy/kun, grafiklar, tushunchalar.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse

from .services import (
    get_insights_for_user,
    get_daily_totals,
    get_category_totals_for_period,
    get_monthly_trend,
)
from expenses.services import get_monthly_totals, get_category_breakdown

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
    daily_nonzero_count = sum(1 for d in daily if d["total"] > 0)

    years = list(range(today.year - 2, today.year + 2))
    months = list(range(1, 13))
    month_choices = list(zip(months, MONTH_NAMES))
    selected_month_name = MONTH_NAMES[month - 1] if 1 <= month <= 12 else ""

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
            "daily_nonzero_count": daily_nonzero_count,
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
