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


@login_required
def statistics_view(request):
    """Umumiy statistika - oy tanlash, kunlik/oylik, grafiklar."""
    today = timezone.now().date()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    view_type = request.GET.get("view", "month")

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

    daily_max = max((d["total"] for d in daily), default=1)
    trend_max = max((t["total"] for t in trend), default=1)

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
        },
    )


@login_required
def chart_data_daily(request):
    """Kunlik grafik ma'lumotlari (API)."""
    year = int(request.GET.get("year", timezone.now().year))
    month = int(request.GET.get("month", timezone.now().month))
    data = get_daily_totals(request.user, year, month)
    return JsonResponse({"data": data})


@login_required
def chart_data_categories(request):
    """Kategoriya grafik ma'lumotlari."""
    today = timezone.now().date()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    from calendar import monthrange
    start = today.replace(year=year, month=month, day=1)
    _, ld = monthrange(year, month)
    end = today.replace(year=year, month=month, day=min(ld, today.day))
    data = get_category_totals_for_period(request.user, start, end)
    return JsonResponse({"data": data})
