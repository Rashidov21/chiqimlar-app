"""
Bildirishnomalar - Telegram orqali xabar yuborish.
"""
import logging
import os
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger(__name__)


def send_telegram_message(telegram_id: int, text: str) -> bool:
    """Foydalanuvchiga Telegram orqali xabar yuboradi."""
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token or not telegram_id:
        return False
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(
            url,
            json={"chat_id": telegram_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.warning("telegram send failed status=%s body=%s", resp.status_code, resp.text[:300])
            return False
        try:
            payload = resp.json()
        except Exception:
            logger.warning("telegram send failed: invalid json response")
            return False
        return bool(payload.get("ok"))
    except Exception:
        return False


def send_telegram_document(telegram_id: int, file_path: str, caption: str = "") -> bool:
    """Foydalanuvchiga Telegram orqali hujjat yuboradi."""
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token or not telegram_id or not file_path:
        return False
    try:
        import requests

        url = f"https://api.telegram.org/bot{token}/sendDocument"
        data = {"chat_id": telegram_id}
        if caption:
            data["caption"] = caption
        with open(file_path, "rb") as f:
            files = {"document": (os.path.basename(file_path), f)}
            resp = requests.post(url, data=data, files=files, timeout=30)
        if resp.status_code != 200:
            logger.warning(
                "telegram sendDocument failed status=%s body=%s",
                resp.status_code,
                resp.text[:300],
            )
            return False
        try:
            payload = resp.json()
        except Exception:
            logger.warning("telegram sendDocument failed: invalid json response")
            return False
        return bool(payload.get("ok"))
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
