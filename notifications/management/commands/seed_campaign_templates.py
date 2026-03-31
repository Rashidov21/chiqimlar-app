from urllib.parse import urlparse
from django.conf import settings
from django.core.management.base import BaseCommand

from notifications.models import CampaignMessageTemplate


TEMPLATES = [
    ("promo_new_1", "new", "insight", "Siz uchun premium insightlar tayyor: oy yakuni razbor va 12 oylik trend Donater'da ochiladi."),
    ("promo_new_2", "new", "report", "Har oy tayyor hisobot botga kelishini xohlaysizmi? Donater bo'lsangiz auto oy yakuni report olasiz."),
    ("promo_new_3", "new", "forecast", "Bu oy temp bo'yicha oldindan ogohlantirish olish uchun Donater funksiyalarini yoqing."),
    ("promo_active_1", "active", "insight", "Siz aktiv foydalanuvchisiz. Endi keyingi daraja: oy yakuni moliyaviy razbor cardi va aniq tavsiyalar."),
    ("promo_active_2", "active", "household", "Family / Household Pro bilan umumiy sarf trendini ko'ring va xarajatlarni birga nazorat qiling."),
    ("promo_active_3", "active", "report", "Donater Pro hisobotda Top 3 tejash nuqtasi chiqadi. Bir oyda real natija ko'rish osonlashadi."),
    ("promo_active_4", "active", "forecast", "Hozirgi tempda oy oxirida limit oshadimi? Donater forecast buni oldindan ko'rsatadi."),
    ("promo_active_5", "active", "insight", "Donater cardida oy yakuni razbor: nima yaxshi bo'ldi, qayerda oshdi, keyingi qadam."),
    ("promo_active_6", "active", "report", "Auto oy yakuni hisobotni botga olsangiz moliyaviy nazorat ancha osonlashadi."),
    ("promo_active_7", "active", "household", "Household Pro: bir nechta a'zo xarajatlarini bitta joyda ko'rib boring."),
    ("promo_active_8", "active", "forecast", "Limitga yaqinlashganda oldindan signal olish uchun Donater funksiyalarini yoqing."),
    ("promo_inactive_1", "inactive", "insight", "Qaytib kelganingizdan xursandmiz. Oxirgi davr bo'yicha premium razbor bilan nazoratni tiklang."),
    ("promo_inactive_2", "inactive", "report", "Qisqa yo'l: Donater yoqib, oy yakuni hisobotni botga tayyor holatda oling."),
    ("promo_inactive_3", "inactive", "household", "Agar oilaviy byudjetni boshqarsangiz, Household Pro sizga juda qulay bo'ladi."),
    ("promo_inactive_4", "inactive", "forecast", "Kelasi oy rejasini xotirjam qilish uchun Donater prognoz kartasini sinab ko'ring."),
    ("promo_inactive_5", "inactive", "insight", "Premium statistikalar bilan qayerda tejash mumkinligini tez topasiz."),
    ("promo_inactive_6", "inactive", "report", "12 oylik trend va pro hisobotlar faqat Donater uchun ochiq."),
    ("promo_new_4", "new", "household", "Agar oilaviy byudjet yuritsangiz, Donater'dagi Family/Household sizga juda mos."),
    ("promo_new_5", "new", "insight", "2 daqiqada premium insightlarni yoqing: oy yakuni razbor va trendlar sizni kutmoqda."),
    ("promo_new_6", "new", "report", "Donater orqali har oy avtomatik hisobot oling va natijani oson solishtiring."),
]


class Command(BaseCommand):
    help = "Promo kampaniya message template'larini yaratadi yoki yangilaydi."

    def handle(self, *args, **options):
        raw = (getattr(settings, "TELEGRAM_WEBAPP_URL", "") or "").strip()
        parsed = urlparse(raw)
        if parsed.scheme and parsed.netloc:
            landing_url = f"{parsed.scheme}://{parsed.netloc}/donater/"
        else:
            landing_url = "/donater/"
        created = 0
        updated = 0
        for key, segment, topic, text in TEMPLATES:
            obj, is_created = CampaignMessageTemplate.objects.update_or_create(
                key=key,
                defaults={
                    "segment": segment,
                    "topic": topic,
                    "text": text,
                    "cta_url": landing_url,
                    "is_active": True,
                    "weight": 1,
                },
            )
            if is_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Template seed tugadi. created={created}, updated={updated}"))
