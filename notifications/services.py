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
