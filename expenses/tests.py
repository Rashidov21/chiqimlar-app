"""Xarajatlar testlari."""
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from categories.models import Category
from .models import Expense
from .services import get_monthly_totals
from decimal import Decimal


class ExpenseServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_monthly_totals_empty(self):
        data = get_monthly_totals(self.user)
        self.assertEqual(data["total_spent"], Decimal("0"))
        self.assertEqual(data["budget"], Decimal("0"))
        self.assertEqual(data["remaining"], Decimal("0"))

    def test_monthly_totals_with_expense(self):
        cat = Category.objects.create(user=self.user, name="Ovqat", emoji="🍔")
        from django.utils import timezone
        today = timezone.now().date()
        Expense.objects.create(user=self.user, category=cat, amount=50000, date=today)
        self.user.monthly_budget = 100000
        self.user.save()
        data = get_monthly_totals(self.user)
        self.assertEqual(data["total_spent"], Decimal("50000"))
        self.assertEqual(data["remaining"], Decimal("50000"))
