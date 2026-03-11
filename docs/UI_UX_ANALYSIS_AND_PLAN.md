# UI/UX — Chuqur tahlil va yechim rejasi

Loyiha: Chiqimlar (mobile-first, Telegram Mini App). Tahlil 20 yillik UI/UX va frontend tajriba asosida.

---

## 1. Register sahifasi kerak emas (authentication bot orqali)

### Tahlil
- Kirish faqat Telegram Mini App orqali: initData → POST `/api/telegram-auth/` → session. Alohida parol yoki ro‘yxatdan o‘tish formasi ishlatilmaydi.
- `/register/` sahifasi mavjud va faqat “botga /start yuboring” tipidagi ma’lumotni ko‘rsatadi; unda forma yo‘q.
- Agar register sahifasiga hech qanday link bo‘lmasa ham, foydalanuvchi URL ni bilganda yoki xatolik natijasida kelsa, “keraksiz” sahifa ko‘rinadi va loyiha kontekstida chalkashlik tug‘diradi.

### Yechim rejasi
- **Variant A (tavsiya):** Register URL’ini saqlab qolish, lekin view’da `redirect('accounts:login')` qilish — `/register/` kelsa avtomatik login sahifasiga yo‘naltirish. Login sahifasi allaqachon “Telegram orqali kirish” ni tushuntiradi.
- **Variant B:** Register URL’ini butunlay olib tashlash (urls.py’dan comment yoki o‘chirish). Agar qandaydir tashqi link `/register/` ga yo‘naltirsa, 404 yoki login’ga redirect.
- **Natija:** Foydalanuvchi faqat bitta kirish nuqtasi (login) ko‘radi; ro‘yxatdan o‘tish kontseptsiyasi bot orqali bo‘lgani uchun alohida “Register” sahifasi talab qilinmaydi.

---

## 2. Tugmalar hajmi va normallashtirish (Saqlash, Bekor qilish va boshqalar)

### Tahlil
- **Hozirgi holat:** `base.html` da `.btn-primary`, `.btn-secondary` (padding 10px 18px, font 0.95rem), `.btn-sm` (8px 14px, 0.875rem), `.btn-lg` (14px 24px, 1rem). Formalar ichida ba’zi joylarda `btn-primary btn-lg` + `width: 100%`, boshqa joylarda `btn-secondary btn-sm`, “Bekor qilish” esa oddiy `<a>` (font 0.9rem) — vizual va tactile jihatdan turlicha.
- **Muammo:** Bir xil semantic (asosiy amal vs ikkinchi darajali) turli sahifalarda turli o‘lchamda; mobilda barmoq bilan bosish uchun minimal 44×44px tavsiya etiladi, ba’zi tugmalar kichik qolishi mumkin.
- **Loyiha konteksti:** Mobile-first, barcha asosiy amallar (Saqlash, Qo‘shish) bir xil darajada muhim; ikkinchi darajali (Bekor qilish, Tahrir) ham aniq va barqaror bo‘lishi kerak.

### Yechim rejasi
- **Tugma ierarxiyasi va o‘lchamlari:**
  - **Primary (asosiy amal):** bitta standart — masalan, min-height 48px, padding 12px 20px, font-size 1rem; border-radius davom etadi (pill). Barcha “Saqlash”, “Qo‘shish”, “Davom etish” shu klass.
  - **Secondary (ikkinchi amal):** min-height 44px, padding 10px 18px, font 0.9375rem — “Bekor qilish”, “Tahrir”, ro‘yxatlardagi ikkinchi tugmalar.
  - **Small (ro‘yxat ichidagi yordamchi):** padding 8px 14px, font 0.875rem — faqat joy yetmasa yoki juda ikkinchi darajali amallar uchun.
- **Qoidalar:** Formadagi asosiy submit — doim primary, to‘liq kenglik (width: 100%) mobilda. “Bekor qilish” — secondary yoki matn link (lekin touch uchun min-height 44px bo‘lgan blok). Barcha sahifalarda “Saqlash”/“Qo‘shish” bir xil primary, “Bekor” bir xil secondary.
- **Qilish:** `base.html` da `.btn-primary`, `.btn-secondary`, `.btn-sm`, `.btn-lg` qiymatlarini yangi standartga moslashtirish; keyin barcha template’lardagi tugmalarni tekshirib, keraksiz inline style’lar (masalan, alohida box-shadow) olib tashlash yoki global qoidaga keltirish.

---

## 3. Main content pastki qismi bottom-nav ostida qolishi

### Tahlil
- **Hozirgi CSS:** `main { padding-bottom: calc(100px + 28px + env(safe-area-inset-bottom, 0px)); }` — 100px bottom-nav balandligi, 28px qo‘shimcha, safe-area. Bottom-nav `position: fixed; bottom: 0`, shuning uchun main kontenti uning ustiga to‘g‘ri kelsa, pastki margin/padding yetmasa oxirgi qatorlar nav ostida qoladi.
- **Sabab:** 100px taxminiy; nav ichidagi linklar padding va font o‘lchamiga qarab haqiqiy balandlik 56–64px atrofida bo‘lishi mumkin. “100px + 28px” ortiqcha berilgan bo‘lishi ham mumkin, lekin ba’zi qurilmalarda (notch, gesture bar) safe-area katta bo‘ladi. Asosiy muammo — ba’zi sahifalarda content juda uzun (masalan, ro‘yxatlar, sozlamalar) va scroll qilganda eng pastki element (masalan, pagination yoki oxirgi kartochka) nav bilan yopilib qolishi.
- **Boshqa omil:** `form-actions-sticky` bilan formaning “Saqlash” bloki sticky bottom’da; u ham safe-area-inset-bottom ishlatadi. Asosiy content esa faqat main’ning padding-bottom’iga tayanadi — agar main ichida yana pastga margin bo‘lmasa, scroll oxirida kontentning oxirgi pikseli navning tepa chetidagi 100px dan pastda bo‘lmaydi; ammo ba’zi brauzerlar yoki viewport’larda hisoblash noto‘g‘ri bo‘lishi mumkin.

### Yechim rejasi
- **Aniqlashtirish:** Bottom-nav uchun aniq balandlik class qo‘shish (masalan, `.bottom-nav` ga `min-height: 56px` va padding’lar orqali haqiqiy balandlikni o‘lchash). Main’ning `padding-bottom` ni shu qiymat + 24px (yoki 32px) + `env(safe-area-inset-bottom)` qilish.
- **Minimum padding:** Scroll oxirida kontent va nav o‘rtasida kamida 16–24px bo‘sh joy ko‘rinsin. Ya’ni `padding-bottom` = bottom-nav haqiqiy balandlik + 24px + safe-area-inset-bottom.
- **Tekshirish:** Uzun sahifalarda (expense_list, debt_list, settings, category_budget_list) scrollni eng pastga tushirganda oxirgi element (pagination, tugma, kartochka) bottom-nav dan aniq yuqorida va o‘qilishi oson bo‘lishini qo‘lda tekshirish.
- **Qilish:** base.html’da main padding-bottom’ni yangi formulaga keltirish; kerak bo‘lsa bottom-nav’ga aniq height/min-height berish va bir marta real qurilmada o‘lchab tasdiqlash.

---

## 4. Mobilda ko‘rinmayotgan linklar (Maqsadlar, Qayta to‘lov, Qarzlar, Maxfiylik, Yordam) — Sozlamalar sahifasida ko‘rsatish

### Tahlil
- **Hozir:** Desktop’da (768px+) yuqori nav’da Maqsadlar, Qayta to‘lov, Qarzlar, Statistika, Turkumlar, Sozlamalar bor. 767px va unda yuqori nav `display: none`, faqat bottom-nav — unda 5 ta: Bu Oy, Qo‘shish, Statistika, Turkumlar, Sozlamalar. Demak, mobilda Maqsadlar, Qayta to‘lov, Qarzlar linklari yo‘q. Maxfiylik va Yordam hech qayerda link emas.
- **Foydalanuvchi ta’siri:** Telefonda faqat dashboard’dagi “Batafsil →” orqali yoki to‘g‘ri URL ni bilish orqali bu bo‘limlarga borish mumkin; yangi foydalanuvchi “Qarzlar qayerda?” deb qidiradi.
- **Yechim taklifi:** Barcha muhim linklarni bitta joyda — Sozlamalar sahifasida — “Ilova bo‘limlari” yoki “Tezkor havolalar” sifatida chiqarish. Shu orqali mobil foydalanuvchi ham Maqsadlar, Qayta to‘lov, Qarzlar, Barcha xarajatlar, Turkumlar, Turkum byudjetlari, Maxfiylik, Yordam’ga bora oladi.

### Yechim rejasi
- **Sozlamalar sahifasiga yangi blok:** “Bo‘limlar” yoki “Tezkor kirish” sarlavhasi ostida ro‘yxat:
  - Bu Oy (dashboard)
  - Xarajat qo‘shish
  - Barcha xarajatlar
  - Maqsadlar
  - Qayta to‘lovlar
  - Qarzlar
  - Statistika
  - Turkumlar
  - Turkum byudjetlari
  - Maxfiylik siyosati (link `/privacy/`)
  - Yordam (link `/yordam/`)
- **Ko‘rinishi:** Har biri qisqa matn + o‘ngda strelka yoki chevron; bir xil card/list uslubida, Sozlamalar’dagi boshqa bloklar (Kirish, Turkumlar, Eksport) kabi. Mobilda barmoq bilan osongina bosiladigan balandlikda.
- **Natija:** Bitta sahifa (Sozlamalar) barcha muhim yo‘nalishlarni birlashtiradi; nav’da bo‘lmagan Maqsadlar/Qayta to‘lov/Qarzlar va hozircha hech qayerda yo‘q Maxfiylik/Yordam ham mavjud bo‘ladi.

---

## 5. Loyiha tematikasi uchun color palette

### Tahlil
- **Hozirgi ranglar:** `:root` da — bg-page #f5f5ff, bg-card #fff, border #e8e6ff / #f3f3ff, text-main #121331, text-muted #6b6b8a, primary #5a3fff, primary-soft #ebe6ff, danger #dc2626. Tailwind’da primary 50–900 binafsha tonlari.
- **Mavzu:** Shaxsiy moliya / xarajatlar — ishonch, soddalik, “ortiqcha sarf” ogohlantirish (danger), ijobiy (yutuq, qolgan byudjet). Hozirgi binafsha yaxshi tanlangan, lekin palitrani yanada tizimlashtirish va kontrast/accessibility ni tekshirish kerak.

### Yechim rejasi
- **Asosiy palitra (nomlar va vazifalar):**
  - **Primary:** Asosiy amal va brend (tugma, link, aktiv holat). Hozirgi #5a3fff saqlanishi mumkin; yoki biroz yumshoqroq (masalan #6366f1) — kontrast tekshiriladi.
  - **Primary soft / bg:** Primary’ning yengil varianti (nav active, alert success) — #ebe6ff yoki #eef2ff.
  - **Background:** Sahifa fon — neytral yengil (#f8fafc yoki #f5f5ff); karta oq yoki 1px border bilan ajratilgan.
  - **Text primary:** Asosiy matn — qora’ga yaqin (#0f172a yoki #121331).
  - **Text muted:** Ikkinchi darajali matn — #64748b yoki #6b7280.
  - **Border:** Subtle — #e2e8f0 yoki #e8e6ff.
  - **Success:** Qolgan byudjet, ijobiy holat — yashil (#16a34a yoki #22c55e).
  - **Danger:** Limit oshishi, xato — qizil (#dc2626).
  - **Warning:** Ogohlantirish (90% byudjet) — sariq/to‘q sariq (#ca8a04 yoki #eab308).
- **Qilish:** Barcha ranglarni `:root` va Tailwind config’da shu nomlar va hex qiymatlar bilan belgilash; template’lardagi qattiq kodlangan hex’larni CSS variable yoki Tailwind class’larga almashtirish. Kontrast (WCAG AA) matn/fon juftliklarida tekshirish.

---

## 6. SVG ikonkalardan foydalanish

### Tahlil
- **Hozir:** Bootstrap Icons (font) — `<i class="bi bi-*">`. Yaxshi coverage, lekin font ikonlar rang va o‘lchamda cheklovchi, ba’zi qurilmalarda pixel perfect bo‘lmasligi mumkin; SVG esa vektor, rang va o‘lchamda aniqroq boshqarish mumkin.
- **Afzallik:** SVG — bir xil o‘lchamda aniqroq, theme rangiga osongina moslashtirish (currentColor yoki fill), accessibility (title/aria). Loyiha mobile-first va Telegram WebView’da ishlaydi — kichik ekranda ikonkaning aniq ko‘rinishi muhim.

### Yechim rejasi
- **Yondashuv:** Inline SVG yoki SVG sprite (symbol/use). Sprite bitta fayl, har bir ikonka `<symbol id="icon-*">` va sahifada `<svg><use href="#icon-*"/></svg>` — bir marta yuklanadi.
- **Ikonka to‘plami:** Barcha hozirgi `bi-*` ishlatiladigan joylarni ro‘yxatga olish (wallet, plus, bullseye, arrow-repeat, people, bar-chart, folder, gear, check, pencil, trash, house, bell, file-excel va boshqalar). Ularning ekvivalenti SVG (Heroicons, Phosphor yoki loyiha uchun tanlangan set) tanlanadi va sprite yoki alohida komponentlar sifatida qo‘shiladi.
- **Almashtirish:** Bir bosqichda: base.html’da sprite faylini ulash, nav va asosiy sahifalarda `bi` o‘rniga SVG’ga o‘tish. Keyin boshqa sahifalar. Yoki aralash qoldirish (font faqat qolgan joylarda) va yangi qismlarda faqat SVG.
- **O‘lcham va rang:** Barcha SVG’lar `width`/`height` (masalan 20, 24) va `currentColor` yoki `fill: var(--primary)` — tema rangiga avtomatik moslashadi.

---

## 7. Summalarni xonalarga ajratib ko‘rsatish (kiritish va UI)

### Tahlil
- **Ko‘rsatish:** Hozir `intcomma` (Django humanize) ishlatiladi — ming ajratuvchi. O‘zbekiston odatida bo‘sh joy yoki vergul (1 000 000 yoki 1,000,000). Locale sozlamasi kerak; brauzerda ko‘rsatishda format bir xil bo‘lishi kerak.
- **Kiritish:** Input’da `type="number"` — xonalar ajratilmaydi, faqat raqam. Katta summa kiritganda (masalan 2000000) o‘qish qiyin; xato ehtimoli oshadi.

### Yechim rejasi
- **Ko‘rsatish (UI):** Barcha summa ko‘rsatiladigan joylarda (dashboard, ro‘yxatlar, kartochkalar) `intcomma` yoki JavaScript’da formatlash (masalan, `toLocaleString('uz-UZ')` yoki maxsus format) — natija doim bo‘sh joy/vergul bilan (1 234 567 so‘m).
- **Kiritish (form):**
  - **Variant A:** Input’da `type="text"` + mask yoki formatlash — foydalanuvchi yozganda avtomatik bo‘sh joy qo‘yiladi; submit’da qiymatdan raqamlar ajratib olinadi va backend’ga son yuboriladi.
  - **Variant B:** `type="number"` qoldirish, lekin placeholder’da namuna: "1 234 567". Yoki input’dan keyin yonida “formatted” ko‘rsatish (masalan, “2 000 000 so‘m”) — faqat ko‘rsatish, input o‘zi number.
- **Qilish:** Backend’da saqlash doim son (Decimal/Integer); frontend’da ko‘rsatish va (agar tanlansa) kiritishda formatlash. Django’da humanize va locale ni tekshirish; kerak bo‘lsa JavaScript’da format/parse funksiyalari.

---

## 8. Summa kiritishda tezkor tanlash (oldingi yoki shablon summalar)

### Tahlil
- **Muammo:** Har safar to‘liq summa yozish — vaqt talab qiladi va xato ehtimoli bor. Tez-tez ishlatiladigan summalar (100 000, 500 000, 1 000 000) yoki oxirgi kiritilgan 2–3 ta summa bo‘lsa, bir bosishda tanlash UX ni yaxshilaydi.
- **Qayerda kerak:** Xarajat qo‘shish/tahrir (amount), oylik byudjet (settings, onboarding), qarz summa, jamg‘arma maqsad (target/current), qayta to‘lov summa, turkum byudjeti.

### Yechim rejasi
- **Shablon summalar:** Har bir summa input’i uchun (yoki faqat asosiy formalar: xarajat, byudjet, qarz) “Tez tanlash” qatori: chip/tugma ko‘rinishida 100 000 | 500 000 | 1 000 000 | 2 000 000 (loyiha tilida). Tugmani bosganda input to‘ldiriladi (yoki input’ga qo‘shiladi).
- **Oxirgi kiritilgan:** Backend’dan foydalanuvchining oxirgi 2–3 ta xarajat summalari (yoki boshqa tegishli model) API yoki context orqali beriladi; sahifada “So‘ngi: 150 000, 75 000, 200 000” kabi chip’lar. Chip bosilganda shu summa tanlanadi.
- **Implementatsiya:** Frontend’da input ustida yoki ostida qator; backend’da (ixtiyoriy) “oxirgi summalar” endpoint yoki view context’da. Shablon summalar faqat frontend’da konstantalar bo‘lishi mumkin.
- **Joylashtirish:** Xarajat forma, sozlamalar byudjet, qarz forma, maqsad forma, qayta to‘lov forma — har birida summa maydoni bor sahifalarda bir xil pattern (tez tanlash + ixtiyoriy oxirgi).

---

## 9. Faqat mobil breakpoint’lar (telefonlar uchun)

### Tahlil
- **Hozir:** `min-width: 768px` da bottom-nav yashirin, top-nav ko‘rinadi; `max-width: 767px` da aksincha. Demak, planchet va desktop uchun ham layout bor.
- **Talab:** Loyiha faqat telefonlarda ishlatiladi (Telegram Mini App, mobile-first) — barcha sahifalar faqat mobil breakpoint’lar uchun moslashtirilsin.

### Yechim rejasi
- **Maqsad:** Bitta “mobile” layout — keng ekranlarda ham mobil ko‘rinish saqlanadi (markazlashgan, bir ustun, bottom-nav doim ko‘rinsa ham yoki keng ekranda ham pastda). Yoki keng ekranda oddiy markazlashgan max-width (masalan 420px) blok, orqa fon neytral.
- **Qadamlar:**
  - Media query’larni soddalashtirish: faqat `max-width` (masalan 430px) uchun maxsus o‘zgarishlar kerak bo‘lsa qo‘llash; `min-width: 768px` dagi “desktop” layout’ni olib tashlash yoki minimal qoldirish (faqat markazlashgan container).
  - Top-nav: mobilda ham ko‘rinishi mumkin (qisqaroq, logo + burger yoki faqat logo) yoki butunlay olib tashlanadi va faqat bottom-nav qoladi.
  - Container: Barcha sahifalarda `max-width: 480px` yoki 420px, margin: 0 auto — katta ekranda ham markazda tor ustun.
- **Natija:** Dizayn faqat mobil uchun; planchet/desktop’da “mobil ko‘rinish” markazda yoki to‘liq kenglikda (bir ustun) ko‘rinadi, ikki ustunli yoki keng nav rejasi ishlatilmaydi.

---

## Amalga oshirish tartibi (reja)

| Tartib | Band | Qisqacha | Bog‘liqlik |
|--------|------|----------|------------|
| 1 | Register | Register view’ni login’ga redirect qilish (yoki URL o‘chirish) | Mustaqil |
| 2 | Tugma normallashtirish | base.html + barcha template’larda btn o‘lchamlari va rollari | Mustaqil |
| 3 | Bottom-nav / main padding | padding-bottom va nav height aniqlashtirish, uzun sahifalarda tekshirish | Mustaqil |
| 4 | Sozlamalar: linklar bloki | Maqsadlar, Qayta to‘lov, Qarzlar, Xarajatlar, Turkumlar, Byudjetlar, Maxfiylik, Yordam | Mustaqil |
| 5 | Color palette | :root va Tailwind yangilash, qattiq kodlangan ranglarni variable/class ga | 6, 7 dan oldin yaxshi |
| 6 | SVG ikonkalar | Sprite yoki inline SVG, nav va asosiy sahifalarda almashtirish | 5 dan keyin |
| 7 | Summa formatlash | Ko‘rsatish (intcomma/locale), kiritish (mask yoki display) | 8 dan oldin |
| 8 | Tezkor summa tanlash | Shablon + ixtiyoriy oxirgi summalar, tegishli formalarda | 7 dan keyin |
| 9 | Faqat mobil layout | Media query soddalash, container, nav yagona mobil rejim | 2, 3, 4 bilan birga yoki oxirida |

**Tavsiya:** Avval 1–4 (tez va foydalanuvchiga sezilarli), keyin 5–6 (dizayn va ikonkalar), so‘ng 7–8 (summa UX), oxirida 9 (layout yagona mobil).

---

## Xulosa

- Register: kerak emas — redirect yoki o‘chirish.
- Tugmalar: bitta standart (primary/secondary/size) loyiha bo‘yicha.
- Main/bottom-nav: padding va nav balandligi aniq, oxirgi content ko‘rinsin.
- Mobil linklar: Sozlamalar’da barcha bo‘limlar + Maxfiylik + Yordam.
- Ranglar: bitta tematik palitra, CSS variable, kontrast tekshirish.
- Ikonkalar: SVG sprite/use, theme rangiga mos.
- Summa: ko‘rsatishda format, kiritishda ixtiyoriy format/mask.
- Tezkor summa: shablon (100k, 500k, 1M) + ixtiyoriy oxirgi 2–3 summa.
- Layout: faqat mobil breakpoint’lar, keng ekranda markazlashgan bir ustun.

Barcha o‘zgarishlar mobile-first va Telegram Mini App kontekstida foydalanuvchi uchun soddalik va tezkor ishlashni maqsad qiladi.
