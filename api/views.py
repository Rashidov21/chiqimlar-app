"""
REST API — minimal GET endpointlar, barcha queryset'lar request.user ga bog'langan.
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from expenses.models import Expense, SavingGoal, Debt
from expenses.services import get_monthly_totals
from .serializers import ExpenseSerializer, SavingGoalSerializer, DebtSerializer


class ExpenseViewSet(viewsets.ReadOnlyModelViewSet):
    """Xarajatlar ro'yxati va bitta xarajat (GET)."""
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        return (
            Expense.objects.filter(user=self.request.user)
            .select_related("category")
            .order_by("-date", "-created_at")
        )


class SavingGoalViewSet(viewsets.ReadOnlyModelViewSet):
    """Jamg'arma maqsadlari (GET)."""
    serializer_class = SavingGoalSerializer

    def get_queryset(self):
        return (
            SavingGoal.objects.filter(user=self.request.user)
            .order_by("-is_active", "-created_at")
        )


class DebtViewSet(viewsets.ReadOnlyModelViewSet):
    """Qarzlar (GET)."""
    serializer_class = DebtSerializer

    def get_queryset(self):
        return Debt.objects.filter(user=self.request.user).order_by("is_closed", "due_date", "-created_at")


class DashboardSummaryViewSet(viewsets.ViewSet):
    """Dashboard qisqacha summary — oylik byudjet va xarajat."""

    def list(self, request):
        user = request.user
        year, month = None, None
        try:
            if request.query_params.get("year"):
                year = int(request.query_params.get("year"))
            if request.query_params.get("month"):
                month = int(request.query_params.get("month"))
        except (TypeError, ValueError):
            pass
        data = get_monthly_totals(user, year=year, month=month)
        return Response({
            "total_spent": str(data["total_spent"]),
            "budget": str(data["budget"]),
            "remaining": str(data["remaining"]),
            "year": data["year"],
            "month": data["month"],
        })
