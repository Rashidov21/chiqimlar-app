"""Xarajatlar testlari."""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache

from accounts.models import User
from categories.models import Category

from .models import Expense
from .services import get_monthly_totals


class ExpenseServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        cache.clear()

    def test_monthly_totals_empty(self):
        data = get_monthly_totals(self.user)
        self.assertEqual(data["total_spent"], Decimal("0"))
        self.assertEqual(data["budget"], Decimal("0"))
        self.assertEqual(data["remaining"], Decimal("0"))

    def test_monthly_totals_with_expense(self):
        cache.clear()
        cat = Category.objects.create(user=self.user, name="Ovqat", emoji="🍔")
        today = timezone.now().date()
        Expense.objects.create(user=self.user, category=cat, amount=50000, date=today)
        User.objects.filter(pk=self.user.pk).update(monthly_budget=100000)
        self.user.refresh_from_db()
        self.assertEqual(self.user.monthly_budget, Decimal("100000"))
        cache.clear()
        data = get_monthly_totals(self.user)
        self.assertEqual(data["total_spent"], Decimal("50000"))
        self.assertEqual(data["budget"], Decimal("100000"))
        self.assertEqual(data["remaining"], Decimal("50000"))


class ExportExcelToTelegramTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="exportuser", password="testpass123")
        self.user.telegram_id = None
        self.user.save()

    def test_export_without_telegram_id_redirects_to_settings(self):
        self.client.login(username="exportuser", password="testpass123")
        response = self.client.post(reverse("expenses:export_excel_to_telegram"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("settings", response.url)


class SettingsViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="settingsuser", password="testpass123")

    def test_settings_post_saves_budget_and_notifications(self):
        self.client.login(username="settingsuser", password="testpass123")
        response = self.client.post(
            reverse("expenses:settings"),
            {
                "monthly_budget": "3000000",
                "telegram_notifications": "on",
                "daily_reminder": "on",
                "weekly_summary": "off",
                "limit_warning": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.monthly_budget, 3000000)
        self.assertTrue(self.user.telegram_notifications)
        self.assertTrue(self.user.daily_reminder)
        self.assertFalse(self.user.weekly_summary)
        self.assertTrue(self.user.limit_warning)
