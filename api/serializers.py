"""
REST API serializers — faqat o'qish (GET) uchun.
"""
from rest_framework import serializers
from expenses.models import Expense, SavingGoal, Debt
from categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "emoji", "order"]


class ExpenseSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "amount",
            "note",
            "date",
            "category",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class SavingGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingGoal
        fields = [
            "id",
            "name",
            "target_amount",
            "current_amount",
            "start_date",
            "target_date",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class DebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debt
        fields = [
            "id",
            "kind",
            "counterparty",
            "amount",
            "date",
            "due_date",
            "note",
            "is_closed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
