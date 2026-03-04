"""
Bildirishnomalar - Telegram orqali xabar yuborish.
"""
from django.conf import settings


def send_telegram_message(telegram_id: int, text: str) -> bool:
    """Foydalanuvchiga Telegram orqali xabar yuboradi."""
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token or not telegram_id:
        return False
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": telegram_id, "text": text, "parse_mode": "HTML"}, timeout=10)
        return True
    except Exception:
        return False


def send_daily_reminder(user):
    """Kunlik eslatma - xarajat kiritish."""
    if not user.telegram_notifications or not user.daily_reminder or not user.telegram_id:
        return
    text = "📝 Salom! Bugun xarajatlaringizni yozib oldingizmi? Chiqimlar botida tez qo'shing."
    send_telegram_message(user.telegram_id, text)


def send_weekly_summary(user, total_spent, by_category):
    """Haftalik xulosa."""
    if not user.telegram_notifications or not user.weekly_summary or not user.telegram_id:
        return
    lines = [f"📊 Haftalik xulosa: jami {int(total_spent):,} so'm sarflandi."]
    for name, amount in by_category[:5]:
        lines.append(f"  • {name}: {int(amount):,} so'm")
    send_telegram_message(user.telegram_id, "\n".join(lines))


def send_limit_warning(user, spent, budget, percent):
    """Byudjet chegarasiga yaqunlashganda ogohlantirish."""
    if not user.telegram_notifications or not user.limit_warning or not user.telegram_id:
        return
    text = f"⚠️ Diqqat! Byudjetingizning {percent:.0f}% ini sarfladingiz ({int(spent):,} / {int(budget):,} so'm)."
    send_telegram_message(user.telegram_id, text)


def maybe_send_limit_warning_after_expense(user):
    """
    Xarajat saqlangandan keyin chaqiriladi. Agar joriy oy byudjetning >= 90% sarflangan
    bo'lsa va limit_warning yoqilgan bo'lsa, Telegram'da ogohlantirish yuboradi.
    Har bir user uchun 24 soat ichida ko'pi bilan 1 marta yuboriladi (cache).
    """
    from django.core.cache import cache
    from expenses.services import get_monthly_totals

    if not user.telegram_notifications or not user.limit_warning or not user.telegram_id:
        return
    totals = get_monthly_totals(user)
    budget = totals["budget"] or 0
    if budget <= 0:
        return
    spent = totals["total_spent"]
    percent = float(spent / budget * 100)
    if percent < 90:
        return
    from django.utils import timezone
    now = timezone.now()
    cache_key = f"limit_warn_{user.pk}_{now.year}_{now.month}"
    if cache.get(cache_key):
        return
    send_limit_warning(user, spent, budget, percent)
    cache.set(cache_key, 1, timeout=86400)  # 24 soat
