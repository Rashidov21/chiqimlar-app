"""Telegram bot testlari."""
from django.test import TestCase
from unittest.mock import patch
from .handlers import process_update, handle_start


class TelegramHandlerTest(TestCase):
    def test_process_update_start(self):
        with patch("telegram_bot.handlers._send_message", return_value=True):
            with patch("accounts.models.VerificationCode.generate") as mock_gen:
                mock_gen.return_value = type("VC", (), {"code": "ABC123"})()
                update = {
                    "message": {
                        "chat": {"id": 123},
                        "from": {"first_name": "Test"},
                        "text": "/start",
                    }
                }
                process_update(update)
                mock_gen.assert_called_once_with(123)
