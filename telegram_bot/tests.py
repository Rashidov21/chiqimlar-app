"""Telegram bot testlari."""
from django.test import TestCase
from unittest.mock import patch
from .handlers import process_update, handle_start


class TelegramHandlerTest(TestCase):
    def test_process_update_start(self):
        """ /start da _send_message chaqiriladi (Mini App tugmasi)."""
        with patch("telegram_bot.handlers._send_message", return_value=True) as mock_send:
            update = {
                "message": {
                    "chat": {"id": 123},
                    "from": {"first_name": "Test"},
                    "text": "/start",
                }
            }
            process_update(update)
            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
            self.assertEqual(args[0], 123)
            self.assertIn("Chiqimlarni ochish", args[1] or "")
