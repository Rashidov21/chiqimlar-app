"""
Xarajatlar - Dashboard, CRUD, sozlamalar.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

from .models import Expense
from .forms import ExpenseForm
from .services import get_monthly_totals, get_category_breakdown
from analytics.services import get_insights_for_user
from notifications.services import (
    maybe_send_limit_warning_after_expense,
    maybe_send_expense_confirmation_after_expense,
)


MONTH_NAMES = [
    "", "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
]


@login_required
def dashboard(request):
    """Bu Oy - asosiy dashboard."""
    today = timezone.now().date()
    date_str = request.GET.get("date") or ""
    selected_date = today
    if date_str:
        try:
            selected_date = datetime.fromisoformat(date_str).date()
        except ValueError:
            selected_date = today
    data = get_monthly_totals(request.user, year=selected_date.year, month=selected_date.month)
    breakdown = get_category_breakdown(request.user, year=selected_date.year, month=selected_date.month)
    recent = (
        Expense.objects.filter(user=request.user)
        .select_related("category")
        .order_by("-date", "-created_at")[:10]
    )
    insights = get_insights_for_user(request.user, limit=3)
    days_count = max((data["month_end"] - data["month_start"]).days + 1, 1)
    avg_daily = data["total_spent"] / days_count if data["total_spent"] > 0 else Decimal("0")
    top_categories = breakdown[:3]
    month_display = f"{MONTH_NAMES[data['month']]} {data['year']}"
    return render(
        request,
        "expenses/dashboard.html",
        {
            "totals": data,
            "month_display": month_display,
            "selected_date_display": f"{selected_date.day} {MONTH_NAMES[selected_date.month].lower()} {selected_date.year}",
            "selected_date_iso": selected_date.isoformat(),
            "breakdown": breakdown,
            "recent": recent,
            "insights": insights,
            "avg_daily": avg_daily,
            "top_categories": top_categories,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def expense_add(request):
    form = ExpenseForm(request.POST or None, user=request.user)
    if form.is_valid():
        expense = form.save()
        maybe_send_limit_warning_after_expense(request.user)
        maybe_send_expense_confirmation_after_expense(request.user, expense)
        messages.success(request, "Xarajat qo'shildi.")
        if request.GET.get("next"):
            return redirect(request.GET["next"])
        return redirect("expenses:dashboard")
    return render(request, "expenses/expense_form.html", {"form": form, "title": "Xarajat qo'shish"})


@login_required
@require_http_methods(["GET", "POST"])
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    form = ExpenseForm(request.POST or None, instance=expense, user=request.user)
    if form.is_valid():
        expense = form.save()
        maybe_send_limit_warning_after_expense(request.user)
        maybe_send_expense_confirmation_after_expense(request.user, expense)
        messages.success(request, "Xarajat yangilandi.")
        return redirect("expenses:dashboard")
    return render(request, "expenses/expense_form.html", {"form": form, "expense": expense, "title": "Xarajatni tahrirlash"})


@login_required
@require_http_methods(["POST"])
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    expense.delete()
    messages.success(request, "Xarajat o'chirildi.")
    return redirect(request.POST.get("next", "expenses:dashboard"))


@login_required
def expense_list(request):
    """Barcha xarajatlar (pagination)."""
    qs = Expense.objects.filter(user=request.user).select_related("category").order_by("-date", "-created_at")
    paginator = Paginator(qs, 20)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)
    return render(request, "expenses/expense_list.html", {"page_obj": page_obj})


@login_required
def export_view(request):
    """CSV eksport."""
    import csv
    from django.http import HttpResponse
    from django.utils import timezone
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="chiqimlar.csv"'
    response.write("\ufeff")  # BOM for Excel UTF-8
    writer = csv.writer(response)
    writer.writerow(["Sana", "Turkum", "Summa", "Izoh"])
    qs = (
        Expense.objects.filter(user=request.user)
        .select_related("category")
        .order_by("-date", "-created_at")
    )
    for e in qs:
        writer.writerow([e.date, e.category.name if e.category else "", e.amount, e.note or ""])
    return response


@login_required
@require_http_methods(["GET", "POST"])
def settings_view(request):
    """Sozlamalar - oylik limit, kod almashtirish, kategoriyalar, eksport."""
    user = request.user
    if request.method == "POST":
        monthly_budget = request.POST.get("monthly_budget")
        if monthly_budget is not None:
            try:
                user.monthly_budget = int(monthly_budget)
                messages.success(request, "Oylik byudjet yangilandi.")
            except (ValueError, TypeError):
                pass
        user.telegram_notifications = request.POST.get("telegram_notifications") == "on"
        user.daily_reminder = request.POST.get("daily_reminder") == "on"
        user.weekly_summary = request.POST.get("weekly_summary") == "on"
        user.limit_warning = request.POST.get("limit_warning") == "on"
        user.save(update_fields=["monthly_budget", "telegram_notifications", "daily_reminder", "weekly_summary", "limit_warning"])
        return redirect("expenses:settings")
    return render(request, "expenses/settings.html", {"user": user})
