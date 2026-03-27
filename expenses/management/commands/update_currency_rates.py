from decimal import Decimal

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

from expenses.models import ExchangeRate


CBU_RATES_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
TRACKED_CURRENCIES = {"USD", "EUR", "RUB"}


def _to_decimal(value) -> Decimal | None:
    text = str(value or "").strip().replace(",", ".")
    if not text:
        return None
    try:
        return Decimal(text)
    except Exception:
        return None


class Command(BaseCommand):
    help = "CBU API dan USD/EUR/RUB kurslarini yangilaydi (UZS ga)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            dest="date_str",
            default="",
            help="Sana (YYYY-MM-DD). Bo'sh bo'lsa bugungi sana ishlatiladi.",
        )

    def handle(self, *args, **options):
        date_str = (options.get("date_str") or "").strip()
        target_date = timezone.now().date()
        if date_str:
            try:
                target_date = timezone.datetime.fromisoformat(date_str).date()
            except ValueError:
                self.stdout.write(self.style.ERROR("Noto'g'ri sana formati. YYYY-MM-DD ishlating."))
                return

        try:
            resp = requests.get(CBU_RATES_URL, timeout=20)
            resp.raise_for_status()
            rows = resp.json() or []
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Kurslarni olishda xatolik: {e}"))
            return

        saved = 0
        for row in rows:
            code = str((row or {}).get("Ccy") or "").upper().strip()
            if code not in TRACKED_CURRENCIES:
                continue
            rate = _to_decimal((row or {}).get("Rate"))
            nominal = _to_decimal((row or {}).get("Nominal")) or Decimal("1")
            if not rate or nominal <= 0:
                continue
            # APIdagi Rate odatda nominal birlik uchun bo'ladi.
            normalized = (rate / nominal).quantize(Decimal("0.000001"))
            ExchangeRate.objects.update_or_create(
                date=target_date,
                currency=code,
                defaults={"rate_to_uzs": normalized, "source": "cbu"},
            )
            saved += 1

        if saved == 0:
            self.stdout.write(self.style.WARNING("Hech qanday kurs saqlanmadi (USD/EUR/RUB topilmadi)."))
            return

        self.stdout.write(self.style.SUCCESS(f"Kurslar yangilandi: {saved} ta ({target_date})."))
