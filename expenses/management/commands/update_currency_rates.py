import logging
import time
from decimal import Decimal

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from expenses.models import ExchangeRate

logger = logging.getLogger(__name__)

DEFAULT_CBU_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
TRACKED_CURRENCIES = {"USD", "EUR", "RUB"}

REQUEST_HEADERS = {
    "User-Agent": "ChiqimlarBudget/1.0 (currency-update; +https://github.com)",
    "Accept": "application/json, text/plain, */*",
}


def _to_decimal(value) -> Decimal | None:
    text = str(value or "").strip().replace(",", ".")
    if not text:
        return None
    try:
        return Decimal(text)
    except Exception:
        return None


def _fetch_cbu_json():
    url = getattr(settings, "CBU_RATES_URL", None) or DEFAULT_CBU_URL
    retries = max(1, int(getattr(settings, "CBU_REQUEST_RETRIES", 3)))
    timeout = float(getattr(settings, "CBU_REQUEST_TIMEOUT", 45.0))
    proxy_raw = getattr(settings, "CBU_REQUEST_PROXY", None) or ""
    proxies = None
    if proxy_raw.strip():
        p = proxy_raw.strip()
        proxies = {"http": p, "https": p}

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url,
                headers=REQUEST_HEADERS,
                proxies=proxies,
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json() or [], url, attempt
        except Exception as e:
            last_error = e
            logger.warning(
                "CBU so'rovi muvaffaqiyatsiz (urinish %s/%s): %s",
                attempt,
                retries,
                e,
            )
            if attempt < retries:
                delay = min(8.0, 2.0 ** (attempt - 1))
                time.sleep(delay)
    raise last_error


class Command(BaseCommand):
    help = "CBU API dan USD/EUR/RUB kurslarini yangilaydi (UZS ga). Proxy va qayta urinish: .env (CBU_REQUEST_PROXY, ...)."

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

        if (getattr(settings, "CBU_REQUEST_PROXY", None) or "").strip():
            self.stdout.write("CBU so'rovi CBU_REQUEST_PROXY orqali yuboriladi.")

        try:
            rows, used_url, attempt_used = _fetch_cbu_json()
            self.stdout.write(f"Manba: {used_url} (muvaffaqiyatli urinish: {attempt_used})")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    "Kurslarni olishda xatolik: {}\n"
                    "Tekshiring: curl -v \"{}\" | head\n"
                    "Agar timeout bo'lsa — boshqa tarmoqdan proxy qo'ying (CBU_REQUEST_PROXY).".format(
                        e,
                        getattr(settings, "CBU_RATES_URL", DEFAULT_CBU_URL),
                    )
                )
            )
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
