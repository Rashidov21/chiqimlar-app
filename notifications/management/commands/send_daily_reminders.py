"""
Kunlik eslatma - barcha sozlamasi yoqilgan foydalanuvchilarga Telegram orqali xabar.
VPS da cron bilan ishlatish: har kuni masalan 18:00 da
  0 18 * * * cd /path/to/chiqimlar-app && .venv/bin/python manage.py send_daily_reminders
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from notifications.services import send_daily_reminder


User = get_user_model()


class Command(BaseCommand):
    help = "Kunlik eslatma yuboradi (Telegram) — daily_reminder=True va telegram_id bo'lgan user'larga."

    def handle(self, *args, **options):
        users = User.objects.filter(
            is_active=True,
            telegram_notifications=True,
            daily_reminder=True,
            telegram_id__isnull=False,
        ).exclude(telegram_id=0)
        count = 0
        for user in users:
            send_daily_reminder(user)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Kunlik eslatma yuborildi: {count} ta foydalanuvchiga"))
