"""
Telegram bot - Webhook orqali komandalar (sinxron).
"""
import logging
import re
import requests
from django.conf import settings
from django.core.cache import cache

from .services import required_channels_ok_for_telegram_id
from .models import RequiredChannel

logger = logging.getLogger(__name__)
WEBAPP_URL = getattr(settings, "TELEGRAM_WEBAPP_URL", "").rstrip("/")
DONATION_NOTE_MAX_LEN = 255


def _shorten_note(text: str, max_len: int = DONATION_NOTE_MAX_LEN) -> str:
    """Donation.note uzunligini xavfsiz chegarada saqlaydi."""
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return text[:max_len]
    return text[: max_len - 1] + "…"


def _extract_amount_from_caption(caption: str) -> int:
    """
    Caption ichidan birinchi yirik sonni topishga urinadi.
    Misol: "50 000", "50000", "120,000 so'm".
    """
    raw = (caption or "").strip()
    if not raw:
        return 0
    candidates = re.findall(r"[\d][\d\s,\.]{1,}", raw)
    if not candidates:
        return 0
    for item in candidates:
        digits = re.sub(r"[^\d]", "", item)
        if not digits:
            continue
        try:
            amount = int(digits)
        except ValueError:
            continue
        # Juda kichik raqamlarni (masalan sana kuni) olib tashlashga urinib ko'ramiz.
        if amount >= 1000:
            return amount
    return 0


def _send_message(chat_id: int, text: str, reply_markup: dict | None = None) -> bool:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:  # pragma: no cover - tarmoq xatolari
        logger.warning("Telegram send_message failed: %s", e)
        return False


def _web_app_keyboard(telegram_id: int) -> dict | None:
    """
    Mini App ochish tugmasi.
    Har bir foydalanuvchi uchun alohida URL (bir martalik login token bilan) yaratiladi.
    """
    if not WEBAPP_URL:
        return None
    try:
        from accounts.services import generate_telegram_login_token
    except Exception:
        # Agar accounts importida muammo bo'lsa, zaxira sifatida oddiy URL'dan foydalanamiz.
        url = WEBAPP_URL
    else:
        try:
            token = generate_telegram_login_token(telegram_id)
            separator = "&" if "?" in WEBAPP_URL else "?"
            url = f"{WEBAPP_URL}{separator}tg_token={token}"
        except Exception:
            url = WEBAPP_URL

    return {
        "keyboard": [
            [{"text": "💰 Chiqimlarni ochish", "web_app": {"url": url}}],
            [{"text": "❤️ Donat qilish"}],
        ],
        "resize_keyboard": True,
    }


def _subscription_keyboard() -> dict:
    """Obuna flow uchun tez tugmalar."""
    return {
        "keyboard": [
            [{"text": "✅ Obuna bo'ldim"}, {"text": "❤️ Donat qilish"}],
        ],
        "resize_keyboard": True,
    }


def _required_channels_text() -> str:
    """
    Majburiy kanallar ro'yxatini foydalanuvchiga ko'rsatish matni.
    """
    channels = RequiredChannel.objects.filter(is_active=True, is_mandatory=True)
    if not channels.exists():
        return (
            "Ilova uchun hozir majburiy kanal yo'q. Agar bu xabarni ko'rsangiz, iltimos, /start ni qayta yuboring "
            "va «Chiqimlarni ochish» tugmasi orqali Mini App ni oching."
        )
    lines: list[str] = [
        "Ilovadan foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling:",
        "",
    ]
    for ch in channels:
        username = (ch.username or "").strip()
        if not username:
            continue
        if not username.startswith("@"):
            username = "@" + username
        lines.append(f"• {ch.name}: {username}")
    lines.append("")
    lines.append(
        "Obuna bo'lgandan keyin Telegram bot chatida yana bir marta /start deb yozing — shundan so'ng «Chiqimlarni "
        "ochish» tugmasi paydo bo'ladi va Mini App orqali ilovaga kirasiz."
    )
    return "\n".join(lines)


def handle_start(chat_id: int, first_name: str = "") -> bool:
    """/start - Mini App tugmasi (avtologin, kanal obunasi shart)."""
    # Avval foydalanuvchi majburiy kanallarga obuna bo'lganini tekshiramiz.
    prev_key = f"sub_prev:{chat_id}"
    prev_status = cache.get(prev_key)
    now_ok = required_channels_ok_for_telegram_id(chat_id)
    cache.set(prev_key, now_ok, 3600)
    if not now_ok:
        text = _required_channels_text()
        text += (
            "\n\nObuna bo'lgach <b>✅ Obuna bo'ldim</b> tugmasini bosing — biz darhol tekshirib beramiz."
        )
        _send_message(chat_id, text, reply_markup=_subscription_keyboard())
        return True

    safe_name = first_name or "do'st"
    text = (
        f"Salom, {safe_name}! 👋\n\n"
        "Pastdagi <b>«Chiqimlarni ochish»</b> tugmasini bosing — ilova ochiladi va siz avtomatik kirasiz. "
        "Ro'yxatdan o'tish ham, kod kiritish ham shart emas. Faqat Telegram profilingiz asosida kirasiz."
    )
    # Agar oldingi holatda obuna bo'lmagan bo'lsa, endi esa bo'lsa — foydalanuvchiga qisqa tasdiq xabari beramiz.
    if prev_status is False and now_ok:
        text = (
            "✅ Obunangiz tasdiqlandi.\n\n"
            + text
        )
    _send_message(chat_id, text, reply_markup=_web_app_keyboard(chat_id))
    return True


def handle_help(chat_id: int) -> bool:
    text = (
        "📌 Buyruqlar:\n"
        "/start — «Chiqimlarni ochish» tugmasi (Mini App avtologin)\n"
        "/help — Yordam\n"
        "/donat — Donat usullari va linklar\n\n"
        "Ilovani ochish: pastdagi tugmani bosing — kod yoki alohida ro'yxatdan o'tish talab qilinmaydi."
    )
    _send_message(chat_id, text)
    return True


def handle_donate(chat_id: int) -> bool:
    """Donat usullari ro'yxati va linklar."""
    from accounts.models import DonationMethod

    methods = DonationMethod.objects.filter(is_active=True).order_by("sort_order", "id")
    if not methods.exists():
        text = "Hozircha donat usullari qo'shilmagan. Keyinroq qayta urinib ko'ring."
        _send_message(chat_id, text)
        return True
    lines = [
        "⭐ <b>Donater bo'ling</b>\n",
        "Ilovani rivojlantirishga yordam bering. To'liq moliyaviy tushunchalar va 12 oylik statistika donat qilganlar uchun. Quyidagi usullar orqali donat qilishingiz mumkin:\n",
    ]
    for m in methods:
        if m.payment_link:
            lines.append(f"• <b>{m.title}</b>\n{m.payment_link}")
    lines.append(
        "\n\u2705 To'lov qilganingizdan so'ng, iltimos <b>chek / to'lov screenshotini</b> aynan shu bot chatiga yuboring.\n"
        "Rasm captionida <b>donat summasini</b> va <b>qaysi usul orqali (masalan, karta/Click/Payme)</b> bo'lganini yozib qo'ying.\n"
        "Admin screenshotni tekshiradi va tasdiqlangach, sizga donater statusini beradi."
    )
    _send_message(chat_id, "\n".join(lines))
    return True


def process_update(update_dict: dict) -> None:
    """Webhook update ni qayta ishlash."""
    message = update_dict.get("message") or {}
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return
    user = message.get("from") or {}
    first_name = user.get("first_name", "")
    text = (message.get("text") or "").strip()

    # 1) Donat chek screenshotlari: foydalanuvchi rasm yuborsa (private chat)
    photos = message.get("photo") or []
    if photos:
        # Faqat private chat uchun ishlaymiz (group/supergroup emas)
        chat_type = (message.get("chat") or {}).get("type")
        if chat_type == "private":
            try:
                from accounts.services import get_or_create_user_by_telegram
                from accounts.models import Donation, DonationMethod
            except Exception as e:  # pragma: no cover - import xatolari loglanadi
                logger.warning("donation_photo: import error: %s", e)
            else:
                try:
                    telegram_id = user.get("id")
                    if telegram_id:
                        app_user = get_or_create_user_by_telegram(
                            telegram_id=telegram_id,
                            first_name=first_name,
                        )
                        caption = (message.get("caption") or "").strip()
                        # Eng katta sifatdagi rasmni olamiz (oxirgisi)
                        best_photo = photos[-1]
                        file_id = best_photo.get("file_id", "")
                        msg_id = message.get("message_id")

                        parsed_amount = _extract_amount_from_caption(caption)
                        parsed_method = None
                        if caption:
                            c_low = caption.lower()
                            active_methods = DonationMethod.objects.filter(is_active=True)
                            for method in active_methods:
                                title = (method.title or "").strip()
                                if title and title.lower() in c_low:
                                    parsed_method = method
                                    break

                        note_parts: list[str] = []
                        if caption:
                            note_parts.append(f"Foydalanuvchi yozuvi: {caption}")
                        if msg_id:
                            note_parts.append(f"Telegram message_id={msg_id}")
                        if file_id:
                            note_parts.append(f"photo_file_id={file_id}")
                        note_text = " | ".join(note_parts) if note_parts else "Telegram chek screenshot (detalsiz)."
                        note_text = _shorten_note(note_text)

                        pending = (
                            Donation.objects.filter(user=app_user, status=Donation.Status.PENDING)
                            .order_by("-created_at")
                            .first()
                        )
                        if pending:
                            pending.note = note_text
                            if parsed_amount > 0:
                                pending.amount = parsed_amount
                            if parsed_method and pending.method_id is None:
                                pending.method = parsed_method
                            pending.save(update_fields=["note", "amount", "method", "confirmed"])
                            donation = pending
                            confirm_text = (
                                "Chek screenshotingiz yangilandi ✅\n\n"
                                "Sizda allaqachon tekshiruvdagi donat bor edi. Biz eng oxirgi yuborgan chek ma'lumotini saqladik. "
                                "Admin tekshiruvni tugatgach donater statusi beriladi."
                            )
                            logger.info(
                                "donation_photo: updated pending donation_id=%s for telegram_id=%s",
                                donation.pk,
                                telegram_id,
                            )
                        else:
                            donation = Donation.objects.create(
                                user=app_user,
                                method=parsed_method,
                                amount=parsed_amount or 0,
                                note=note_text,
                                status=Donation.Status.PENDING,
                            )
                            logger.info(
                                "donation_photo: created donation_id=%s for telegram_id=%s",
                                donation.pk,
                                telegram_id,
                            )
                            confirm_text = (
                                "Rahmat! Donat chek screenshotini qabul qildik ✅\n\n"
                                "Admin to'lovni tekshirib, tasdiqlagandan so'ng sizga donater statusi beriladi. "
                                "Agar captionga donat summasini va qaysi usul (karta/Click/Payme) bo'lganini yozsangiz, "
                                "tekshiruv tezroq bo'ladi."
                            )
                        _send_message(chat_id, confirm_text)
                        return
                except Exception as e:  # pragma: no cover - istalgan xato loglanadi, lekin bot yiqilmaydi
                    logger.exception("donation_photo: error: %s", e)

    # 2) Matnli komandalar
    if text == "/start":
        handle_start(chat_id, first_name)
    elif text == "✅ Obuna bo'ldim":
        handle_start(chat_id, first_name)
    elif text == "❤️ Donat qilish":
        handle_donate(chat_id)
    elif text == "/help":
        handle_help(chat_id)
    elif text == "/donat":
        handle_donate(chat_id)

