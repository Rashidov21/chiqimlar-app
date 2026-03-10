# Ko'p valyutali tizim — dizayn hujjati

Bu hujjat faqat dizayn va reja. Amalga oshirish kodi yozilmagan.

---

## 1. Maqsad

Foydalanuvchilar xarajatlarini turli valyutalarda (so'm, USD, EUR va boshqalar) kiritishlari va barcha hisobotlarni bitta "asosiy" valyutada ko'rishlari mumkin bo'ladi.

---

## 2. Model o'zgarishlari

### 2.1 Valyuta modeli

- **Currency** (yangi model yoki jadval): `code` (ISO 4217, masalan UZS, USD), `name`, `symbol`. Dastlab so'm va kerak bo'lgan boshqa valyutalar qo'lda yoki fixture orqali kiritiladi.

### 2.2 Summa oladigan modellar

Har birida **valyuta** maydoni qo'shiladi (ForeignKey yoki CharField):

| Model | Yangi maydon | Izoh |
|-------|--------------|------|
| **Expense** | `currency` (yoki default = profile'dan) | Xarajat qaysi valyutada |
| **SavingGoal** | `currency` | Maqsad valyutasi |
| **Debt** | `currency` | Qarz valyutasi |
| **RecurringExpense** | `currency` | Takrorlanuvchi summa valyutasi |
| **CategoryBudget** | `currency` yoki umumiy byudjet faqat asosiy valyutada | Qisqalik uchun barcha byudjetlar asosiy valyutada bo'lishi mumkin |

### 2.3 Profil

- **FinanceProfile** (yoki User): `preferred_currency` (asosiy valyuta). Barcha hisobotlar va dashboard shu valyutada ko'rsatiladi. Yangi xarajat kiritilganda default valyuta shu bo'ladi.

---

## 3. Kurs va konvertatsiya

### 3.1 Exchange servis

- **Xizmat**: `core` yoki `expenses` ichida `ExchangeService` (yoki `get_rate`, `convert` funksiyalari).
- **Vazifasi**: Berilgan sana (yoki bugun) uchun `from_currency` → `to_currency` kursini qaytarish; summani konvertatsiya qilish.
- **Manba**: tashqi API (masalan NBU, Open Exchange Rates) yoki qo'lda kiritilgan kurslar jadvali (Admin orqali). Production'da cache (masalan 1 soat) tavsiya etiladi.

### 3.2 Kurs jadvali (ixtiyoriy)

- **ExchangeRate** modeli: `date`, `from_currency`, `to_currency`, `rate`. Bu orqali tarixiy kurslar saqlanadi va hisobotlar aniqroq bo'ladi.

---

## 4. Biznes-mantiq

- Xarajat kiritilganda: foydalanuvchi valyutani tanlaydi (yoki default `preferred_currency`). Summa va valyuta saqlanadi.
- Dashboard / hisobotlar: barcha summalar `preferred_currency` ga konvertatsiya qilinadi (berilgan sana bo'yicha kurs orqali), keyin yig'indilar hisoblanadi.
- Byudjet: `monthly_budget` va turkum byudjetlari asosiy valyutada (preferred_currency) bo'ladi; xarajatlar konvertatsiya qilingach solishtiriladi.

---

## 5. API va UI

- **REST API**: GET endpoint'larida summa + valyuta qaytariladi; dashboard summary'da ixtiyoriy parametr `?currency=UZS` yoki default profil asosiy valyutasi.
- **UI**: Xarajat formada valyuta tanlash (dropdown); dashboard'da barcha raqamlar asosiy valyutada + ixtiyoriy "asl valyutada" ko'rsatish.

---

## 6. Xavfsizlik va cheklovlar

- Kurs manbai ishonchli bo'lishi kerak; xatolikda eski kurs yoki "kurs topilmadi" xabari.
- Valyuta ro'yxati admin orqali boshqariladi yoki faqat whitelist (UZS, USD, EUR) qo'yiladi.

---

## 7. Keyingi qadamlar (implementatsiya tartibi)

1. `Currency` modeli va `FinanceProfile.preferred_currency` (migration).
2. `Expense.currency` (va kerak bo'lsa boshqa modellar) + default qiymat.
3. `ExchangeService` + tashqi API yoki `ExchangeRate` jadvali.
4. Dashboard va hisobotlarda konvertatsiya qo'llash.
5. Form va API'da valyuta qo'shish va testlar.
