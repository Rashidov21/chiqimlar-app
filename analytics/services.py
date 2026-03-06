"""
Tahlil - Moliyaviy tushunchalar va statistikalar.
"""
from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone
from django.db.models.functions import TruncDate
from collections import defaultdict


def get_insights_for_user(user, year=None, month=None, limit=5):
    """
    Foydalanuvchi uchun qisqa moliyaviy tushunchalar (matn).
    Masalan: "Ovqat xarajatlari bu oy 20% oshdi"
    """
    today = timezone.now().date()
    year = year or today.year
    month = month or today.month
    insights = []

    # Oy boshidan beri va o'tgan oy
    this_start = today.replace(year=year, month=month, day=1)
    if month == 1:
        prev_start = this_start.replace(year=year - 1, month=12, day=1)
        prev_end = this_start - timezone.timedelta(days=1)
    else:
        prev_start = this_start.replace(month=month - 1, day=1)
        prev_end = this_start - timezone.timedelta(days=1)
    from datetime import date
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    this_end = date(year, month, last_day)
    if year == today.year and month == today.month:
        this_end = min(today, this_end)

    qs_this_period = user.expenses.filter(date__gte=this_start, date__lte=this_end)
    this_total = qs_this_period.aggregate(s=Sum("amount"))["s"] or Decimal("0")
    prev_total = (
        user.expenses.filter(date__gte=prev_start, date__lte=prev_end)
        .aggregate(s=Sum("amount"))["s"]
        or Decimal("0")
    )

    # Byudjet ogohlantirish
    budget = user.monthly_budget or Decimal("0")
    if budget > 0 and this_total >= budget:
        insights.append("⚠️ Bu oy byudjetingiz tugadi. Keyingi oyga ehtiyotkorroq sarflang.")
    elif budget > 0 and this_total >= budget * Decimal("0.9"):
        insights.append("📊 Byudjetingizning 90% dan ko'pi sarflandi. Oxirgi kunlarda tejang.")

    # O'tgan oyga nisbatan o'sish/kamayish
    if prev_total > 0:
        change_pct = ((this_total - prev_total) / prev_total) * 100
        if change_pct > 15:
            insights.append(f"📈 O'tgan oyga nisbatan xarajatlar {change_pct:.0f}% oshdi.")
        elif change_pct < -15:
            insights.append(f"📉 O'tgan oyga nisbatan xarajatlar {abs(change_pct):.0f}% kamaydi. Ajoyib!")

    # Kunlik o'rtacha xarajat
    days_count = max((this_end - this_start).days + 1, 1)
    if this_total > 0 and days_count > 0:
        avg_daily = this_total / days_count
        insights.append(
            f"📆 Kuniga o'rtacha {avg_daily.quantize(Decimal('1')):,.0f} so'm sarflayapsiz."
        )

    # Turkum bo'yicha eng ko'p sarflangan
    from categories.models import Category
    cat_totals = []
    for cat in Category.objects.filter(user=user):
        s = (
            cat.expenses.filter(date__gte=this_start, date__lte=this_end)
            .aggregate(s=Sum("amount"))["s"]
            or Decimal("0")
        )
        if s > 0:
            cat_totals.append((cat, s))
    cat_totals.sort(key=lambda x: x[1], reverse=True)
    if cat_totals and this_total > 0:
        top_cat, top_sum = cat_totals[0]
        pct = (top_sum / this_total) * 100
        insights.append(
            f"🍔 {top_cat.emoji} {top_cat.name} — bu oy xarajatlaringizning {pct:.0f}% ini tashkil qiladi."
        )

    # Kichik-cheklar (mayda xarajatlar) bo'yicha ogohlantirish
    small_qs = qs_this_period.filter(amount__lte=Decimal("50000"))
    small_count = small_qs.count()
    if small_count >= 5:
        small_total = small_qs.aggregate(s=Sum("amount"))["s"] or Decimal("0")
        if small_total > 0:
            insights.append(
                f"🧾 {small_count} ta kichik-cheklar (≤ 50 000 so'm) jami {int(small_total):,} so'm. Ularni rejalashtirsangiz tejash mumkin."
            )

    # Eng "qimmat" kun
    daily_qs = (
        qs_this_period.annotate(day=TruncDate("date"))
        .values("day")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    if daily_qs:
        top_day = daily_qs[0]
        if top_day["total"] and this_total > 0 and top_day["total"] >= this_total * Decimal(
            "0.25"
        ):
            insights.append(
                f"🔥 {top_day['day']} kuni juda ko'p xarajat bo'lgan — {int(top_day['total']):,} so'm."
            )

    return insights[:limit]


def get_daily_totals(user, year, month):
    """Oy kunlari bo'yicha jami (grafik uchun) — har bir kalendar kuni alohida."""
    from calendar import monthrange

    start = timezone.datetime(year, month, 1).date()
    _, last_day = monthrange(year, month)
    end = timezone.datetime(year, month, last_day).date()

    qs = (
        user.expenses.filter(date__gte=start, date__lte=end)
        .values("date")
        .annotate(total=Sum("amount"))
        .order_by("date")
    )
    by_date = {item["date"]: item["total"] for item in qs}

    result = []
    d = start
    while d <= end:
        result.append({"date": d, "total": by_date.get(d, Decimal("0"))})
        d += timezone.timedelta(days=1)
    return result


def get_category_totals_for_period(user, start_date, end_date):
    """Davr bo'yicha turkumlar yig'indisi (pasta grafik)."""
    from categories.models import Category
    result = []
    for cat in Category.objects.filter(user=user):
        s = (
            cat.expenses.filter(date__gte=start_date, date__lte=end_date)
            .aggregate(s=Sum("amount"))["s"]
            or Decimal("0")
        )
        if s > 0:
            result.append({"name": f"{cat.emoji} {cat.name}", "total": float(s), "slug": cat.pk})
    return result


MONTH_NAMES_SHORT = [
    "Yan", "Fev", "Mar", "Apr", "May", "Iyn",
    "Iyl", "Avg", "Sen", "Okt", "Noy", "Dek",
]


def get_monthly_trend(user, months=6):
    """Oxirgi N oy uchun oylik jami (trend grafik)."""
    from datetime import date
    from calendar import monthrange
    today = timezone.now().date()
    result = []
    for i in range(months - 1, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        start = date(y, m, 1)
        _, ld = monthrange(y, m)
        end = date(y, m, ld)
        end = min(end, today)
        s = user.expenses.filter(date__gte=start, date__lte=end).aggregate(s=Sum("amount"))["s"] or Decimal("0")
        label = f"{MONTH_NAMES_SHORT[m - 1]} {y}" if 1 <= m <= 12 else f"{y}-{m:02d}"
        result.append({"year": y, "month": m, "total": float(s), "label": label})
    return result
