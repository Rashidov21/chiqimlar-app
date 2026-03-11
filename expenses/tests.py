"""Xarajatlar testlari."""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache

from accounts.models import User
from categories.models import Category

from .models import Expense, SavingGoal
from .services import get_dashboard_context, get_monthly_totals


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


class DashboardContextTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser2", password="testpass123")

    def test_dashboard_context_contains_active_goals(self):
        ctx = get_dashboard_context(self.user)
        self.assertIn("active_goals", ctx)
        self.assertEqual(len(ctx["active_goals"]), 0)

    def test_dashboard_context_active_goals_list(self):
        today = timezone.now().date()
        SavingGoal.objects.create(
            user=self.user,
            name="Maqsad 1",
            target_amount=1000000,
            current_amount=200000,
            start_date=today,
            is_active=True,
        )
        ctx = get_dashboard_context(self.user)
        self.assertEqual(len(ctx["active_goals"]), 1)
        self.assertEqual(ctx["active_goals"][0].name, "Maqsad 1")


class SavingGoalListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser3", password="testpass123")

    def test_saving_goal_list_returns_200(self):
        self.client.login(username="testuser3", password="testpass123")
        response = self.client.get(reverse("expenses:saving_goal_list"))
        self.assertEqual(response.status_code, 200)

    def test_saving_goal_list_ordering(self):
        today = timezone.now().date()
        SavingGoal.objects.create(
            user=self.user, name="A", target_amount=100, current_amount=90,
            start_date=today, is_active=True,
        )
        SavingGoal.objects.create(
            user=self.user, name="B", target_amount=100, current_amount=50,
            start_date=today, is_active=True,
        )
        self.client.login(username="testuser3", password="testpass123")
        response = self.client.get(reverse("expenses:saving_goal_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("page_obj", response.context)
        goals = list(response.context["page_obj"])
        self.assertEqual(len(goals), 2)


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
