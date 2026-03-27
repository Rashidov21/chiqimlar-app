from decimal import Decimal
from django.conf import settings


SUPPORTED_CURRENCIES = (
    ("UZS", "So'm (UZS)"),
    ("USD", "Dollar (USD)"),
    ("EUR", "Euro (EUR)"),
    ("RUB", "Rubl (RUB)"),
)


def get_currency_rates_to_uzs() -> dict[str, Decimal]:
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
    return rates


def convert_to_uzs(amount, currency: str) -> Decimal:
    rates = get_currency_rates_to_uzs()
    code = (currency or "UZS").upper()
    rate = rates.get(code, Decimal("1"))
    return (Decimal(amount) * rate).quantize(Decimal("1"))
