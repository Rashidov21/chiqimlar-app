"""
Turkumlar uchun yordamchi funksiyalar.
"""
from .models import Category


DEFAULT_CATEGORIES = [
    ("Ovqat", "🍔", 0),
    ("Transport", "🚗", 1),
    ("Uy / Ijara", "🏠", 2),
    ("Sog'liq", "💊", 3),
    ("Ta'lim", "📚", 4),
    ("Boshqa", "📌", 5),
]


def create_default_categories(user):
    """
    Foydalanuvchida turkum bo'lmasa, standart turkumlarni yaratadi.
    Onboarding tugagach yoki birinchi foydalanishda chaqiriladi.
    """
    if Category.objects.filter(user=user).exists():
        return
    for name, emoji, order in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            user=user,
            name=name,
            defaults={"emoji": emoji, "order": order},
        )
