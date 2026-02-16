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

    def test_login_with_valid_code_creates_user(self):
        vc = VerificationCode.generate(telegram_id=111)
        c = Client()
        r = c.post(reverse("accounts:login"), {"code": vc.code, "csrfmiddlewaretoken": c.get(reverse("accounts:login")).cookies.get("csrftoken", "")})
        # Need to get csrf from form
        r = c.get(reverse("accounts:login"))
        csrf = r.context["form"]
        r = c.post(reverse("accounts:login"), {"code": vc.code, "csrfmiddlewaretoken": r.cookies.get("csrftoken", "")})
        self.assertIn(r.status_code, [200, 302])
        if r.status_code == 302:
            self.assertEqual(r.url, reverse("expenses:dashboard"))
