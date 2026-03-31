"""
Bildirishnomalar - xabar yuborish (Telegram va boshqa kanallar sender orqali).
"""
import logging
import random
from decimal import Decimal
from datetime import datetime, time, timedelta

from django.utils import timezone
from .models import CampaignMessageTemplate, CampaignDeliveryLog, UserCampaignState
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


PROMO_MAX_PER_WEEK = 3
PROMO_MIN_HOURS_BETWEEN_SENDS = 48
PROMO_MAX_HOURS_BETWEEN_SENDS = 84
PROMO_QUIET_HOURS_START = 22
PROMO_QUIET_HOURS_END = 9


def _segment_for_user(user):
    age_days = (timezone.now() - user.date_joined).days
    if age_days <= 3:
        return CampaignMessageTemplate.Segment.NEW
    from expenses.models import Expense
    active_recently = Expense.objects.filter(
        user=user, created_at__gte=timezone.now() - timedelta(days=7)
    ).exists()
    return CampaignMessageTemplate.Segment.ACTIVE if active_recently else CampaignMessageTemplate.Segment.INACTIVE


def _in_quiet_hours(now):
    hour = now.hour
    return hour >= PROMO_QUIET_HOURS_START or hour < PROMO_QUIET_HOURS_END


def _next_random_send_time(now):
    delta_hours = random.randint(PROMO_MIN_HOURS_BETWEEN_SENDS, PROMO_MAX_HOURS_BETWEEN_SENDS)
    target = now + timedelta(hours=delta_hours)
    target_date = target.date()
    target_hour = random.randint(PROMO_QUIET_HOURS_END, PROMO_QUIET_HOURS_START - 1)
    target_minute = random.randint(0, 59)
    return timezone.make_aware(
        datetime.combine(target_date, time(target_hour, target_minute)),
        timezone.get_current_timezone(),
    )


def _week_start(d):
    return d - timedelta(days=d.weekday())


def _reset_week_if_needed(state, today):
    ws = _week_start(today)
    if state.weekly_window_start != ws:
        state.weekly_window_start = ws
        state.weekly_send_count = 0


def choose_weighted_template(user, state):
    segment = _segment_for_user(user)
    qs = CampaignMessageTemplate.objects.filter(segment=segment, is_active=True)
    if state.last_topic:
        qs = qs.exclude(topic=state.last_topic)
    templates = list(qs)
    if not templates:
        templates = list(CampaignMessageTemplate.objects.filter(is_active=True))
    if not templates:
        return None
    weights = [max(1, t.weight) for t in templates]
    return random.choices(templates, weights=weights, k=1)[0]


def eligible_for_non_donater_promo(user, now=None):
    now = now or timezone.now()
    if not user.is_active or user.is_supporter or not user.telegram_id:
        return False, "not_target"
    if _in_quiet_hours(now):
        return False, "quiet_hours"
    if not getattr(user, "telegram_notifications", True):
        return False, "notifications_off"
    from accounts.models import Donation
    if Donation.objects.filter(user=user, status=Donation.Status.PENDING).exists():
        return False, "pending_donation"
    from expenses.models import Expense
    if Expense.objects.filter(user=user, created_at__gte=now - timedelta(hours=24)).exists():
        return False, "active_last_24h"
    state, _ = UserCampaignState.objects.get_or_create(
        user=user, defaults={"weekly_window_start": _week_start(now.date())}
    )
    if state.promo_opt_out:
        return False, "opt_out"
    _reset_week_if_needed(state, now.date())
    if state.weekly_send_count >= PROMO_MAX_PER_WEEK:
        state.save(update_fields=["weekly_window_start", "weekly_send_count", "updated_at"])
        return False, "weekly_cap"
    if state.next_send_at and now < state.next_send_at:
        return False, "not_due"
    return True, ""


def send_non_donater_promo(user, now=None):
    now = now or timezone.now()
    ok, reason = eligible_for_non_donater_promo(user, now=now)
    state, _ = UserCampaignState.objects.get_or_create(
        user=user, defaults={"weekly_window_start": _week_start(now.date())}
    )
    if not ok:
        CampaignDeliveryLog.objects.create(
            user=user,
            status=CampaignDeliveryLog.Status.SKIPPED,
            skip_reason=reason,
            sent_at=now,
        )
        return False, reason

    template = choose_weighted_template(user, state)
    if not template:
        CampaignDeliveryLog.objects.create(
            user=user,
            status=CampaignDeliveryLog.Status.SKIPPED,
            skip_reason="no_template",
            sent_at=now,
        )
        return False, "no_template"

    text = template.text.strip()
    if template.cta_url:
        text += f"\n\n👉 {template.cta_url}"
    sent = send_telegram_message(user.telegram_id, text)
    if sent:
        _reset_week_if_needed(state, now.date())
        state.weekly_send_count += 1
        state.last_sent_at = now
        state.last_topic = template.topic
        state.next_send_at = _next_random_send_time(now)
        state.save()
        CampaignDeliveryLog.objects.create(
            user=user,
            template=template,
            status=CampaignDeliveryLog.Status.SENT,
            message_text=text,
            sent_at=now,
        )
        return True, "sent"
    CampaignDeliveryLog.objects.create(
        user=user,
        template=template,
        status=CampaignDeliveryLog.Status.FAILED,
        message_text=text,
        sent_at=now,
    )
    return False, "failed"


def get_non_donater_promo_candidates(limit=200):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.filter(
        is_active=True,
        is_supporter=False,
        telegram_id__isnull=False,
        telegram_notifications=True,
    ).exclude(telegram_id=0)[:limit]
