"""
Bildirishnomalar - xabar yuborish (Telegram va boshqa kanallar sender orqali).
"""
import logging
from decimal import Decimal

from .senders import get_default_sender

logger = logging.getLogger(__name__)


def send_telegram_message(telegram_id: int, text: str) -> bool:
    """Foydalanuvchiga Telegram orqali xabar yuboradi (default sender orqali)."""
    return get_default_sender().send_message(telegram_id, text)


def send_telegram_document(telegram_id: int, file_path: str, caption: str = "") -> bool:
    """Foydalanuvchiga Telegram orqali hujjat yuboradi (default sender orqali)."""
    return get_default_sender().send_document(telegram_id, file_path, caption=caption)


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


def maybe_send_expense_confirmation_after_expense(user, expense):
    """
    Har bir yangi / tahrir qilingan xarajatdan so'ng qisqa tasdiqlovchi xabar.
    """
    if not getattr(user, "telegram_notifications", False) or not getattr(user, "telegram_id", None):
        return

    from expenses.services import get_monthly_totals

    totals = get_monthly_totals(user)
    total_spent = totals["total_spent"] or Decimal("0")
    budget = totals["budget"] or Decimal("0")

    category_label = getattr(expense.category, "name", "") or "Turkum tanlanmagan"
    amount = int(expense.amount)

    lines = [
        f"✅ {amount:,} so'm '{category_label}' uchun yozib qo'yildi.",
        f"Bu oy jami: {int(total_spent):,} so'm.",
    ]
    if budget > 0:
        remaining = budget - total_spent
        lines.append(f"Oylik limit: {int(budget):,} so'm, qolgan: {int(remaining):,} so'm.")

    send_telegram_message(user.telegram_id, "\n".join(lines))
