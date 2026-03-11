"""Hisoblar testlari."""
from django.test import TestCase, Client
from django.urls import reverse
from .models import User, VerificationCode
from django.utils import timezone
from datetime import timedelta


class VerificationCodeModelTest(TestCase):
    def test_generate_code(self):
        vc = VerificationCode.generate(telegram_id=12345)
        self.assertEqual(vc.telegram_id, 12345)
        self.assertEqual(len(vc.code), 6)
        self.assertFalse(vc.is_used)
        self.assertGreater(vc.expires_at, timezone.now())

    def test_is_valid(self):
        vc = VerificationCode.generate(telegram_id=999)
        self.assertTrue(vc.is_valid())
        vc.is_used = True
        vc.save()
        self.assertFalse(vc.is_valid())


class LoginViewTest(TestCase):
    def test_login_page_loads(self):
        c = Client()
        r = c.get(reverse("accounts:login"))
        self.assertEqual(r.status_code, 200)

    def test_login_page_get_returns_200(self):
        """Login sahifasi GET da 200 qaytaradi; kontekstda form talab qilinmaydi (Mini App auth)."""
        c = Client()
        r = c.get(reverse("accounts:login"))
        self.assertEqual(r.status_code, 200)
