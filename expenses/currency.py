from decimal import Decimal
from django.conf import settings
from django.core.cache import cache


SUPPORTED_CURRENCIES = (
    ("UZS", "So'm (UZS)"),
    ("USD", "Dollar (USD)"),
    ("EUR", "Euro (EUR)"),
    ("RUB", "Rubl (RUB)"),
)
CURRENCY_RATES_CACHE_KEY = "currency_rates_to_uzs:latest"
CURRENCY_RATES_CACHE_TTL = 21600  # 6 soat


def get_currency_rates_to_uzs() -> dict[str, Decimal]:
    cached = cache.get(CURRENCY_RATES_CACHE_KEY)
    if cached:
        return cached

    raw = getattr(settings, "CURRENCY_RATES_TO_UZS", {}) or {}
    rates: dict[str, Decimal] = {"UZS": Decimal("1")}
    for code, value in raw.items():
        try:
            rates[str(code).upper()] = Decimal(str(value))
        except Exception:
            continue
    rates.setdefault("USD", Decimal("12500"))
    rates.setdefault("EUR", Decimal("13500"))
    rates.setdefault("RUB", Decimal("140"))

    # DB'da yangi kurslar bo'lsa env qiymatlarini override qiladi.
    try:
        from .models import ExchangeRate

        latest_date = ExchangeRate.objects.order_by("-date").values_list("date", flat=True).first()
        if latest_date:
            latest_rates = ExchangeRate.objects.filter(date=latest_date)
            for item in latest_rates:
                rates[(item.currency or "").upper()] = Decimal(str(item.rate_to_uzs))
            rates["UZS"] = Decimal("1")
    except Exception:
        # DB yo'q/migration bo'lmagan holatda env fallback ishlaydi.
        pass

    cache.set(CURRENCY_RATES_CACHE_KEY, rates, timeout=CURRENCY_RATES_CACHE_TTL)
    return rates


def convert_to_uzs(amount, currency: str) -> Decimal:
    rates = get_currency_rates_to_uzs()
    code = (currency or "UZS").upper()
    rate = rates.get(code, Decimal("1"))
    return (Decimal(amount) * rate).quantize(Decimal("1"))
