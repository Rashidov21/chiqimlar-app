# 💰 Chiqimlar — Shaxsiy moliya ilovasi

Shaxsiy xarajatlarni kuzatish, byudjet boshqaruv va Telegram orqali kirish imkoniyatiga ega veb-ilova.

**Muallif:** Abdurahmon Rashidov  
**Vaqt zonasi:** UTC+5 (Asia/Tashkent)  
**Til:** O'zbek

## Imkoniyatlar

- 📊 **Bu Oy** — oylik byudjet, sarflangan summa, qolgan, turkumlar bo'yicha taqsimot
- 📈 **Umumiy statistika** — oy/kun bo'yicha, grafiklar, moliyaviy tushunchalar
- 🗂 **Barcha turkumlar** — kategoriyalar (emoji + nom), tahrirlash/o'chirish
- ⚙️ **Sozlamalar** — oylik limit, Telegram bildirishnomalar, eksport
- 💸 **Xarajatlar** — tez qo'shish, tahrir, o'chirish, kategoriya va sana
- 🔐 **Kirish** — Telegram bot orqali tasdiqlash kodi (kam friction)
- 🔔 **Telegram** — kunlik eslatma, haftalik xulosa, byudjet ogohlantirishi

## Texnologiyalar

- **Backend:** Django 5, PostgreSQL, Django REST (ixtiyoriy)
- **Frontend:** Django templates, Tailwind CSS
- **Telegram:** python-telegram-bot, webhook
- **Infrastructure:** .env, Docker

## O'rnatish

### 1. Klonlash va virtual muhit

```bash
git clone <repo>
cd chiqimlar-app
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Muhit o'zgaruvchilari

```bash
copy .env.example .env
# .env ni tahrirlang: SECRET_KEY, DATABASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_WEBAPP_URL
```

### 3. Ma'lumotlar bazasi

**PostgreSQL** (tavsiya etiladi): `.env` da `DATABASE_URL=postgres://user:password@localhost:5432/chiqimlar_db` bo‘lsin. Lokal:

```bash
# PostgreSQL o'rnatilgan bo'lsa
createdb chiqimlar_db
python manage.py migrate
python manage.py createsuperuser  # ixtiyoriy, admin uchun
```

**SQLite** (tez sinash uchun): `.env` da `DATABASE_URL` ni o‘chiring yoki bo‘sh qoldiring. Keyin `python manage.py migrate`.

### 4. Telegram bot

1. [@BotFather](https://t.me/BotFather) da yangi bot yarating, token oling.
2. `.env` da `TELEGRAM_BOT_TOKEN` va `TELEGRAM_WEBAPP_URL` (masalan `https://your-domain.com`) qo'ying.
3. Webhook o'rnatish (production):  
   `https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-domain.com/telegram/webhook/`  
   Ixtiyoriy: `TELEGRAM_WEBHOOK_SECRET` header yoki query orqali tekshirish.

### 4.1. Telegram Mini App (Web App)

Bu loyiha Telegram Mini App sifatida ham ishlaydi. Sozlash:

1. `.env` da:
   - `TELEGRAM_WEBAPP_URL=https://your-domain.com` (root URL, foydalanuvchi uchun `/` ochiladi, login bo'lmasa `/accounts/login/` ga yo'naltiriladi)
2. [@BotFather](https://t.me/BotFather) da:
   - `/mybots` → botni tanlang → **Bot Settings** → **Menu Button** yoki **Web App** bo'limidan `TELEGRAM_WEBAPP_URL` ni Web App URL sifatida kiriting (agar kanal obunasi qat'iy bo'lsa, bu tugmani o'chirib, faqat botdagi `/start` javobidagi tugmani ishlatishingiz mumkin).
3. Foydalanuvchi `/start` yuborganda bot:
   - Agar majburiy kanallarga obuna bo'lmasa — kanal(lar) ro'yxatini yuboradi
   - Agar obuna bo'lgan bo'lsa — “💰 Chiqimlarni ochish” Web App tugmasini yuboradi (Telegram ichida veb-ilova ochiladi)
4. Mini App ichida:
   - Telegram WebApp SDK yordamida `initData` serverga yuboriladi
   - Backend `initData` imzo va vaqtini tekshiradi, foydalanuvchini Telegram ID bo'yicha yaratadi/topadi va sessiyani ochadi
   - Agar avtomatik login muvaffaqiyatli bo'lmasa, foydalanuvchi ekranda xato turi va keyingi qadamlar (masalan, /start ni qayta yuborish, kanallarga obuna bo'lish) bo‘yicha aniq ko‘rsatmani ko‘radi

### 5. Ishga tushirish

```bash
python manage.py runserver
```

Veb: http://127.0.0.1:8000/  
Kirish: Telegramda botga `/start` yuboring va “Chiqimlarni ochish” tugmasi orqali Mini App'ni oching (initData asosida avtomatik login).

## Docker

```bash
cp .env.example .env
# .env da DATABASE_URL ni postgres://postgres:postgres@db:5432/chiqimlar_db qiling
docker-compose up -d
docker-compose exec web python manage.py migrate
```

## Testlar

```bash
python manage.py test
```

## Eslatmalar (Telegram)

Kunlik eslatma va haftalik xulosa **cron** orqali ishga tushadi. Batafsil: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). VPS da crontab oching (`crontab -e`) va qo‘shing:

```bash
# Har kuni 18:00 da kunlik eslatma (xarajat kiritishni eslatadi)
0 18 * * * cd /path/to/chiqimlar-app && .venv/bin/python manage.py send_daily_reminders

# Har hafta dushanba 09:00 da haftalik xulosa (oxirgi 7 kun)
0 9 * * 1 cd /path/to/chiqimlar-app && .venv/bin/python manage.py send_weekly_summaries
```

`/path/to/chiqimlar-app` o‘rniga loyiha papkasining to‘liq yo‘lini yozing (masalan `/var/www/chiqimlar-app`). Byudjet ogohlantirishi xarajat qo‘shilganda yoki tahrirlanganda avtomatik yuboriladi (byudjetning 90% dan ortiq sarflangan bo‘lsa, 24 soat ichida ko‘pi bilan 1 marta).

**Tekshirish (VPS da):**

```bash
# Qo‘lda ishga tushirib Telegram’da xabar kelishini tekshiring
python manage.py send_daily_reminders
python manage.py send_weekly_summaries
```

Foydalanuvchida `telegram_id` bo‘lishi va Sozlamalarda bildirishnomalar yoqilgan bo‘lishi kerak.

## Loyiha tuzilishi

- `config/` — Django sozlamalari, URL
- `accounts/` — foydalanuvchi, tasdiqlash kodi
- `categories/` — xarajat turkumlari
- `expenses/` — xarajatlar, dashboard, sozlamalar
- `analytics/` — statistika, tushunchalar
- `notifications/` — Telegram xabarlar
- `telegram_bot/` — webhook, /start (Mini App avtologin)
- `templates/` — HTML (base, login, dashboard, statistika, …)

## Muhit o'zgaruvchilari (to'liq ro'yxat)

| O'zgaruvchi | Tavsif | Default |
|-------------|--------|---------|
| `SECRET_KEY` | Django maxfiy kalit | `dev-secret-change-in-production` |
| `DEBUG` | Debug rejim | `True` |
| `ALLOWED_HOSTS` | Ruxsat etilgan hostlar (vergul bilan) | `localhost,127.0.0.1` |
| `DATABASE_URL` | PostgreSQL URL (bo'sh bo'lsa SQLite) | — |
| `TIME_ZONE` | Vaqt zonasi | `Asia/Tashkent` |
| `TELEGRAM_BOT_TOKEN` | Bot token (@BotFather) | — |
| `TELEGRAM_WEBAPP_URL` | Mini App root URL | — |
| `TELEGRAM_WEBHOOK_SECRET` | Webhook himoya (ixtiyoriy) | — |
| `TELEGRAM_INITDATA_MAX_AGE` | initData amal qilish (soniya) | `604800` (7 kun) |
| `REDIS_URL` | Redis (production cache, rate limit) | — |
| `CELERY_BROKER_URL` | Celery broker (ixtiyoriy) | — |
| `SENTRY_DSN` | Sentry xatolik kuzatish (ixtiyoriy) | — |

**Production:** `REDIS_URL` berilsa (masalan `redis://localhost:6379/0`), cache (rate limit, replay himoya, insights, oylik yig‘indilar) Redis’da saqlanadi. Ko‘p worker (gunicorn) ishlatilganda Redis majburiy tavsiya etiladi.

## Hujjatlar

- [Implementatsiya rejasi (sprintlar)](docs/IMPLEMENTATION_PLAN.md) — performance, security, UI/UX va keyingi ishlar rejasi.
- [Multi-currency dizayn](docs/MULTI_CURRENCY_DESIGN.md) — ko‘p valyutali tizim uchun dizayn hujjati.
- [Go-Live checklist](docs/GO_LIVE_CHECKLIST.md) — production deploy va smoke-test nazorat ro'yxati.

Litsenziya: MIT (yoki loyiha qoidalariga qarab).