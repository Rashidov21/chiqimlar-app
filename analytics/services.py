"""
Tahlil - Moliyaviy tushunchalar, statistikalar va yutuqlar.
"""
from decimal import Decimal
from collections import defaultdict

from django.core.cache import cache
from django.db.models import Sum, Q
from django.utils import timezone

from .models import Achievement, UserAchievement


INSIGHTS_CACHE_KEY = "insights:{user_id}:{year}:{month}"
INSIGHTS_CACHE_TTL = 300  # 5 daqiqa


def _compute_insights_for_period(user, year, month, limit=5):
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
        qs_this_period.values("date")
        .annotate(total=Sum("amount"))
        .order_by("-total", "date")
    )
    top_day = daily_qs.first()
    if top_day:
        if top_day["total"] and this_total > 0 and top_day["total"] >= this_total * Decimal(
            "0.25"
        ):
            insights.append(
                f"🔥 {top_day['date']} kuni juda ko'p xarajat bo'lgan — {int(top_day['total']):,} so'm."
            )

    return insights[:limit]


def get_insights_for_user(user, year=None, month=None, limit=5):
    """
    Foydalanuvchi uchun moliyaviy tushunchalar (cache bilan).
    """
    today = timezone.now().date()
    year = year or today.year
    month = month or today.month
    cache_key = INSIGHTS_CACHE_KEY.format(user_id=user.pk, year=year, month=month)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached[:limit]
    insights = _compute_insights_for_period(user, year, month, limit=limit)
    cache.set(cache_key, insights, timeout=INSIGHTS_CACHE_TTL)
    return insights


def clear_insights_cache_for_user(user, year=None, month=None) -> None:
    """
    Berilgan foydalanuvchi uchun moliyaviy tushunchalar cache'ini tozalaydi.
    Agar year/month berilmasa, joriy oy uchun ishlaydi.
    """
    today = timezone.now().date()
    year = year or today.year
    month = month or today.month
    cache_key = INSIGHTS_CACHE_KEY.format(user_id=user.pk, year=year, month=month)
    cache.delete(cache_key)


ACHIEVEMENT_CHECK_CACHE_KEY = "achievement_check_done:"
ACHIEVEMENT_CHECK_CACHE_TTL = 600  # 10 min - tekshiruv har 10 min da max 1 marta


def _grant_new_achievements(user):
    """Yangi yutuqlarni tekshiradi va kerak bo'lsa yozadi (faqat DB)."""
    from django.core.cache import cache
    from expenses.services import get_monthly_totals

    today = timezone.now().date()
    unlocked_codes = set(
        UserAchievement.objects.filter(user=user).values_list("achievement__code", flat=True)
    )

    def _ensure_achievement(code, name, description):
        ach, _ = Achievement.objects.get_or_create(
            code=code,
            defaults={"name": name, "description": description},
        )
        return ach

    if "first_expense" not in unlocked_codes and user.expenses.exists():
        ach = _ensure_achievement(
            "first_expense",
            "Birinchi xarajat yozildi",
            "Ilovada birinchi marta xarajat kiritdingiz.",
        )
        UserAchievement.objects.get_or_create(user=user, achievement=ach)
        unlocked_codes.add("first_expense")

    if "seven_day_streak" not in unlocked_codes:
        dates = set(
            user.expenses.filter(
                date__gte=today - timezone.timedelta(days=6),
                date__lte=today,
            ).values_list("date", flat=True)
        )
        streak_ok = all(
            (today - timezone.timedelta(days=i)) in dates for i in range(7)
        )
        if streak_ok:
            ach = _ensure_achievement(
                "seven_day_streak",
                "7 kun ketma-ket",
                "Ketma-ket 7 kun davomida xarajatlaringizni yozib bordingiz.",
            )
            UserAchievement.objects.get_or_create(user=user, achievement=ach)
            unlocked_codes.add("seven_day_streak")

    if "month_without_overspend" not in unlocked_codes:
        totals = get_monthly_totals(user)
        budget = totals["budget"] or Decimal("0")
        total_spent = totals["total_spent"] or Decimal("0")
        if budget > 0 and total_spent <= budget:
            ach = _ensure_achievement(
                "month_without_overspend",
                "Byudjet ichida oy",
                "Joriy oy byudjetdan oshmadingiz.",
            )
            UserAchievement.objects.get_or_create(user=user, achievement=ach)
            unlocked_codes.add("month_without_overspend")


def get_user_achievements(user, limit=5):
    """
    Foydalanuvchi yutuqlari ro'yxati (faqat o'qish).
    Yangi yutuq berish faqat analytics.signals (Expense post_save) orqali amalga oshadi.
    """
    return list(
        UserAchievement.objects.filter(user=user)
        .select_related("achievement")
        .order_by("-obtained_at")[:limit]
    )


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
    """Davr bo'yicha turkumlar yig'indisi (pasta grafik) — bitta group-by so'rov."""
    from expenses.models import Expense
    from categories.models import Category

    raw = (
        Expense.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date,
            category_id__isnull=False,
        )
        .values("category_id")
        .annotate(s=Sum("amount"))
    )
    totals_by_cat = {row["category_id"]: row["s"] or Decimal("0") for row in raw if row["s"]}
    if not totals_by_cat:
        return []
    categories = Category.objects.filter(
        user=user, id__in=list(totals_by_cat.keys())
    ).order_by("order", "name")
    return [
        {"name": f"{c.emoji} {c.name}", "total": float(totals_by_cat[c.id]), "slug": c.pk}
        for c in categories
    ]


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
