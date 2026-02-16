"""Global context - dashboard uchun byudjet ma'lumotlari."""
from .services import get_monthly_totals


def dashboard_context(request):
    if not request.user.is_authenticated:
        return {}
    data = get_monthly_totals(request.user)
    return {
        "dashboard_budget": data["budget"],
        "dashboard_spent": data["total_spent"],
        "dashboard_remaining": data["remaining"],
    }
