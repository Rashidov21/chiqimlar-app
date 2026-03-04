"""
Haftalik xulosa - oxirgi 7 kun xarajatlari bo'yicha Telegram xabar.
VPS da cron: har hafta masalan dushanba 09:00
  0 9 * * 1 cd /path/to/chiqimlar-app && .venv/bin/python manage.py send_weekly_summaries
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone

from notifications.services import send_weekly_summary

User = get_user_model()


class Command(BaseCommand):
    help = "Haftalik xulosa yuboradi (Telegram) — oxirgi 7 kun xarajatlari."

    def handle(self, *args, **options):
        today = timezone.now().date()
        week_ago = today - timezone.timedelta(days=7)
        users = User.objects.filter(
            is_active=True,
            telegram_notifications=True,
            weekly_summary=True,
            telegram_id__isnull=False,
        ).exclude(telegram_id=0)
        count = 0
        for user in users:
            agg = (
                user.expenses.filter(date__gte=week_ago, date__lte=today)
                .values("category__name", "category__emoji")
                .annotate(total=Sum("amount"))
            )
            total_spent = sum((r["total"] or Decimal("0")) for r in agg)
            by_category = [
                ((f"{r.get('category__emoji') or ''} {r.get('category__name') or 'Boshqa'}").strip() or "Boshqa", r["total"] or 0)
                for r in agg
            ]
            by_category.sort(key=lambda x: -x[1])
            send_weekly_summary(user, total_spent, by_category)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Haftalik xulosa yuborildi: {count} ta foydalanuvchiga"))
