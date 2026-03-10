"""REST API v1 URL'lar — barcha endpoint'lar /api/v1/ ostida."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ExpenseViewSet, SavingGoalViewSet, DebtViewSet, DashboardSummaryViewSet

router = DefaultRouter()
router.register("expenses", ExpenseViewSet, basename="api-expenses")
router.register("goals", SavingGoalViewSet, basename="api-goals")
router.register("debts", DebtViewSet, basename="api-debts")
router.register("dashboard", DashboardSummaryViewSet, basename="api-dashboard")

urlpatterns = [
    path("", include(router.urls)),
]
