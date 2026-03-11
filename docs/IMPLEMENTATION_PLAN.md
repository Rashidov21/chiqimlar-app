# Chiqimlar-app — Implementatsiya rejasi

Yuqoridagi tahlil (UI/UX, Logika, User flow, Performance, Security) asosida keyingi ishlar uchun bosqichli reja.

---

## Umumiy printsip

- **Ustunlik:** Security va Performance birinchi, keyin Logika va UI/UX.
- **Sprint:** Har bir sprint 1–2 hafta (taxminiy), mustaqil deploy qilish mumkin bo‘lgan qismlar.
- **Test:** Har sprint oxirida `manage.py check`, asosiy flow qo‘lda tekshiruv.

---

## Sprint 1 — Performance (asosiy darajada)

**Maqsad:** Context processor, N+1 va debt aggregate’larni optimallashtirish.

| # | Vazifa | Qisqacha | Natija |
|---|--------|----------|--------|
| 1.1 | Context processor cache | `dashboard_context` da `get_monthly_totals` natijasini cache’lash. Kalit: `monthly_totals:{user_id}:{year}:{month}`, TTL 60–120 s. Cache miss’da DB, keyin cache.set. | Har bir sahifada qo‘shimcha so‘rov kamayadi. |
| 1.2 | Debt total’lar aggregate | `get_dashboard_context` va `debt_list` view’da `taken_total` / `given_total` ni Python sum() o‘rniga `Debt.objects.filter(...).aggregate(Sum('amount'))` (kind=TAKEN va GIVEN bo‘yicha 2 ta yoki 1 ta values+annotate) qilish. | Kamroq object yuklash, tezroq javob. |
| 1.3 | get_category_totals_for_period | Analytics `get_category_totals_for_period` ni N+1’siz qilish: `Expense.objects.filter(user, date__gte, date__lte, category_id__isnull=False).values('category_id').annotate(s=Sum('amount'))` + Category.objects.filter(user).order_by() — bitta yoki 2 ta so‘rov. | Statistika sahifasi tezlashadi. |
| 1.4 | Dashboard open_debts | Dashboard’da faqat "qarz holati" matni kerak bo‘lsa, list o‘rniga faqat aggregate; agar "ro‘yxat" ham kerak bo‘lsa, alohida limit’li queryset (masalan 5 ta). | Dashboard’da keraksiz yuklash yo‘q. |

**Sprint 1 yakuni:** Performance tahlilidagi eng og‘ir joylar bartaraf etilgan.

---

## Sprint 2 — Security (rate limit va export)

**Maqsad:** Write action’lar va export uchun rate limit, xavfsizlikni oshirish.

| # | Vazifa | Qisqacha | Natija |
|---|--------|----------|--------|
| 2.1 | Write action’lar rate limit | `expense_edit`, `expense_delete`, `debt_edit`, `debt_delete`, `category_create`, `category_edit`, `category_delete`, `category_budget_*`, `saving_goal_create`, `saving_goal_edit`, `settings_view` POST uchun `@rate_limit_action` (masalan 30/60s yoki 20/60s). Bir xil decorator parametrlari yoki settings’dan o‘qish. | Abuse va avtomatik skanerlar cheklanadi. |
| 2.2 | Export rate limit | `export_view` (CSV) va `export_excel_to_telegram` uchun alohida rate limit (masalan 5/soat yoki 10/daqiqa). IP yoki user asosida. | Export orqali server/Telegram overload kamayadi. |
| 2.3 | Sozlamalar validation | Settings POST’da `monthly_budget` uchun: noto‘g‘ri yoki manfiy bo‘lsa xabar (messages.error) va save qilmaslik; muvaffaqiyatda messages.success. | Foydalanuvchi "saqlandi" xato tushunishi bartaraf. |

**Sprint 2 yakuni:** Security tahlilidagi asosiy bo‘shliqlar yopilgan.

---

## Sprint 3 — Logika va UX (forms, flow)

**Maqsad:** Sozlamalar, onboarding va achievement mantiqini soddalashtirish.

| # | Vazifa | Qisqacha | Natija |
|---|--------|----------|--------|
| 3.1 | Dashboard achievement faqat o‘qish | `get_user_achievements` ichidan `_grant_new_achievements` chaqiruvini olib tashlash; grant faqat `analytics.signals` (post_save Expense) da. Dashboard faqat UserAchievement’larni o‘qiydi. | Bir joyda grant, kod aniqroq. |
| 3.2 | Onboarding "Byudjetsiz davom etish" | Onboarding’da "Keyinroq kiritaman" yoki "Byudjetsiz davom etish" tugmasi: monthly_budget = null/0, onboarding_completed = True, redirect dashboard. Sozlamalar’da byudjet keyinroq kiritiladi. | User flow yaxshilanadi. |
| 3.3 | Export limit (ixtiyoriy) | Export (CSV/Excel) da maksimal sana diapazoni (masalan oxirgi 24 oy) yoki maksimal qator (masalan 10 000). Limitdan oshsa xabar: "Juda ko‘p; oxirgi N oyni tanlang." | Timeout va xotira xavfi kamayadi. |

**Sprint 3 yakuni:** Logika va birinchi darajadagi user flow yaxshilandi.

---

## Sprint 4 — UI/UX (nav, export feedback, xabarlar)

**Maqsad:** Navigatsiya, export holati va form xabarlarini yaxshilash.

| # | Vazifa | Qisqacha | Natija |
|---|--------|----------|--------|
| 4.1 | Nav active holati | Bottom va top nav’da active: `request.resolver_match.url_name` va `request.resolver_match.app_name` (yoki namespace) bo‘yicha aniq tekshiruv. Masalan: analytics:statistics, categories:list. "categories" in path o‘rniga url_name/app. | Faqat bitta link active. |
| 4.2 | Goals / Recurring / Debts kirish | Nav’ga 3 ta link qo‘shish (yoki dropdown "Boshqa") yoki dashboard’dagi bloklarda "Barchasi" linkini aniq qilish. Tanlov: oddiy nav’da "Maqsadlar", "Qayta to‘lovlar", "Qarzlar" yoki faqat dashboard kartalarida "Batafsil →" yetarli ekanini tekshirish. | Foydalanuvchi bu sahifalarni topadi. |
| 4.3 | Export "jarayon" xabari | Excel/Telegram export bosilganda: "Yuborilmoqda..." (disabled tugma yoki spinner); muvaffaqiyat/ xato message mavjud. Agar backend uzoq ishlasa, kamida "So‘rov qabul qilindi" xabari. | Uzoq kutish tushunarli. |
| 4.4 | Form xatolari shablon | Base template yoki snippet: `non_field_errors` va har bir field uchun `field.errors` ko‘rsatish. Kerakli formalarga include. | Xato ko‘rinishi bir xil. |

**Sprint 4 yakuni:** UI/UX tahlilidagi asosiy bandlar bajarilgan.

---

## Sprint 5 — Infrastructure va qo‘shimcha

**Maqsad:** Production cache, pagination, 404/500.

| # | Vazifa | Qisqacha | Natija |
|---|--------|----------|--------|
| 5.1 | Production cache (Redis) | settings’da CACHES: DEBUG=False bo‘lganda Redis (REDIS_URL env). LocMem fallback development uchun. Replay, rate limit, insights, achievements, (ixtiyoriy) monthly_totals cache Redis’da. | Ko‘p worker’da bir xil limit va cache. |
| 5.2 | Pagination (goals, debts, recurring) | saving_goal_list, debt_list, recurring_list’da Paginator (masalan 20–30 ta). GET ?page=, pagination UI (oldingi/keyingi). | Ko‘p yozuvda sahifa tez. |
| 5.3 | 404/500 shablonlar | 404.html, 500.html mobil layout (max-width, padding), uz matn. 500’da umumiy "Xatolik yuz berdi" + LOGIN_URL yoki bosh sahifa linki. | Mobil va tilga mos. |
| 5.4 | Hujjatlashtirish | README yoki docs’da: environment variables, Telegram sozlama, Redis (production), optional Celery. Implementatsiya rejasi (bu fayl) havola. | Yangi developer tez tushunadi. |

**Sprint 5 yakuni:** Production tayyorligi va qulaylik oshdi.

---

## Ixtiyoriy / Keyingi bosqich

- **API Token auth:** DRF TokenAuthentication, token yaratish (admin yoki maxsus endpoint), hujjatda ko‘rsatish.
- **Monitoring:** Sentry (mavjud sozlama), yoki health check endpoint `/health/`.
- **E2E test:** Login → onboarding → xarajat qo‘shish → dashboard (Playwright/Selenium) — ixtiyoriy.

---

## Qisqacha timeline (taxminiy)

| Sprint | Asosiy mavzu   | Muddat (taxminiy) |
|--------|----------------|-------------------|
| 1     | Performance    | 1 hafta            |
| 2     | Security       | 3–5 kun            |
| 3     | Logika / flow  | 1 hafta            |
| 4     | UI/UX          | 1 hafta            |
| 5     | Infra + extra  | 1 hafta            |

Jami: taxminan 4–5 hafta (qisman parallel ishlash mumkin).

---

## Bog‘liqliklar

- Sprint 1 va 2 bir-biriga bog‘liq emas; parallel boshlasa bo‘ladi.
- Sprint 3.1 (achievement) Sprint 1’dan mustaqil; 3.2 (onboarding) esa view + template.
- Sprint 4 nav (4.1, 4.2) base.html va barcha sahifalarga ta’sir qiladi; 4.3 faqat export view + template.
- Sprint 5.1 (Redis) Sprint 1–2’dagi cache/rate limit’dan keyin mantiqan to‘g‘ri (avval LocMem’da ishlatib ko‘rish, keyin Redis’ga o‘tish).

Bu reja tahlil hisobotidagi "Keyingi qilinadigan ishlar" ro‘yxatini sprint’lar va aniq vazifalar ko‘rinishida birlashtiradi; har bir vazifani keyin alohida task/card sifatida ochish mumkin.
