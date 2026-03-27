"""Telegram bot testlari."""
from django.test import TestCase
from unittest.mock import patch

from .handlers import process_update, handle_start


class TelegramHandlerTest(TestCase):
    def test_process_update_start_sends_message(self):
        """`/start` chaqirilganda _send_message chaqiriladi (Mini App tugmasi yoki kanal xabari)."""
        update = {
            "message": {
                "chat": {"id": 123},
                "from": {"first_name": "Test"},
                "text": "/start",
            }
        }
        with patch("telegram_bot.handlers._send_message", return_value=True) as mock_send, patch(
            "telegram_bot.handlers.required_channels_ok_for_telegram_id",
            return_value=True,
        ):
            process_update(update)
            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
            self.assertEqual(args[0], 123)

    def test_handle_start_without_subscription_shows_required_channels_text(self):
        """required_channels_ok_for_telegram_id False bo'lsa, faqat kanal ro'yxati yuboriladi."""
        with patch(
            "telegram_bot.handlers.required_channels_ok_for_telegram_id",
            return_value=False,
        ), patch("telegram_bot.handlers._send_message", return_value=True) as mock_send:
            handle_start(123, "Test")
            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
            # Obuna flow keyboardi yuboriladi.
            reply_markup = kwargs.get("reply_markup") or {}
            self.assertIn("keyboard", reply_markup)
            self.assertIn("✅ Obuna bo'ldim", str(reply_markup))

