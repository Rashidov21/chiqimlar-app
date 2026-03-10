"""
Bildirishnoma kanallari - abstract interface va Telegram implementatsiyasi.
Kelajakda EmailSender va boshqalar qo'shilishi mumkin.
"""
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class BaseSender(ABC):
    """Bildirishnoma yuborish uchun asosiy interface."""

    @abstractmethod
    def send_message(self, recipient_id: Any, text: str) -> bool:
        """Matnli xabar yuboradi. recipient_id kanalga qarab (telegram_id, email va h.k.)."""
        pass

    @abstractmethod
    def send_document(self, recipient_id: Any, file_path: str, caption: str = "") -> bool:
        """Hujjat yuboradi."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Kanal nomi (log va sozlamalar uchun)."""
        pass


class TelegramSender(BaseSender):
    """Telegram Bot API orqali xabar va hujjat yuborish."""

    name = "telegram"

    def __init__(self, token: str | None = None):
        self._token = token or getattr(settings, "TELEGRAM_BOT_TOKEN", None)

    def send_message(self, recipient_id: Any, text: str) -> bool:
        if not self._token or not recipient_id:
            logger.warning("TelegramSender: token yoki recipient_id yo'q")
            return False
        try:
            import requests
            url = f"https://api.telegram.org/bot{self._token}/sendMessage"
            resp = requests.post(
                url,
                json={"chat_id": recipient_id, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
            if resp.status_code != 200:
                logger.warning(
                    "telegram send failed status=%s body=%s",
                    resp.status_code,
                    resp.text[:300],
                )
                return False
            payload = resp.json()
            return bool(payload.get("ok"))
        except Exception as e:
            logger.exception("TelegramSender.send_message: %s", e)
            return False

    def send_document(self, recipient_id: Any, file_path: str, caption: str = "") -> bool:
        if not self._token or not recipient_id or not file_path:
            logger.warning("TelegramSender: token, recipient_id yoki file_path yo'q")
            return False
        if not os.path.isfile(file_path):
            logger.warning("TelegramSender: fayl mavjud emas path=%s", file_path)
            return False
        try:
            import requests
            url = f"https://api.telegram.org/bot{self._token}/sendDocument"
            data = {"chat_id": recipient_id}
            if caption:
                data["caption"] = caption
            with open(file_path, "rb") as f:
                files = {"document": (os.path.basename(file_path), f)}
                resp = requests.post(url, data=data, files=files, timeout=30)
            if resp.status_code != 200:
                logger.warning(
                    "telegram sendDocument failed status=%s body=%s",
                    resp.status_code,
                    resp.text[:300],
                )
                return False
            payload = resp.json()
            return bool(payload.get("ok"))
        except Exception as e:
            logger.exception("TelegramSender.send_document: %s", e)
            return False


def get_default_sender() -> BaseSender:
    """Hozircha faqat Telegram. Keyinchalik sozlamaga qarab Email qo'shiladi."""
    return TelegramSender()
