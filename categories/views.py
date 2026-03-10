from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.permissions import get_user_object_or_404
from expenses.models import Expense
from expenses.services import get_monthly_totals, get_category_breakdown
from .models import Category, CategoryBudget
from .forms import CategoryForm, CategoryBudgetForm


@login_required
def category_list(request):
    """Barcha turkumlar - bu oydagi tranzaksiyalar va summalar bilan."""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    categories = (
        Category.objects.filter(user=request.user)
        .annotate(
            tx_count=Count("expenses", filter=Q(expenses__date__gte=month_start, expenses__date__lte=today)),
            total_spent=Sum("expenses__amount", filter=Q(expenses__date__gte=month_start, expenses__date__lte=today)),
        )
        .order_by("order", "name")
    )
    totals = get_monthly_totals(request.user)
    return render(request, "categories/category_list.html", {"categories": categories, "totals": totals})


@login_required
@require_http_methods(["GET", "POST"])
def category_create(request):
    form = CategoryForm(request.POST or None, user=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Turkum qo'shildi.")
        return redirect("categories:list")
    return render(request, "categories/category_form.html", {"form": form, "title": "Yangi turkum"})


@login_required
@require_http_methods(["GET", "POST"])
def category_edit(request, pk):
    category = get_user_object_or_404(Category, request.user, pk)
    form = CategoryForm(request.POST or None, instance=category, user=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Turkum yangilandi.")
        return redirect("categories:list")
    return render(request, "categories/category_form.html", {"form": form, "category": category, "title": "Turkumni tahrirlash"})


@login_required
@require_http_methods(["POST"])
def category_delete(request, pk):
    category = get_user_object_or_404(Category, request.user, pk)
    category.delete()
    messages.success(request, "Turkum o'chirildi.")
    return redirect("categories:list")


@login_required
def category_budget_list(request):
    """Kategoriya bo'yicha byudjetlar va joriy oy sarflari. Barcha turkumlar ko'rsatiladi (sarf 0 bo'lsa ham)."""
    from calendar import monthrange

    today = timezone.now().date()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        if not (1 <= month <= 12) or not (2000 <= year <= 2100):
            year, month = today.year, today.month
    except (TypeError, ValueError):
        year, month = today.year, today.month

    _, last_day = monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)
    if year == today.year and month == today.month:
        month_end = today

    categories = list(
        Category.objects.filter(user=request.user).order_by("order", "name")
    )
    budgets_qs = CategoryBudget.objects.filter(
        user=request.user, year=year, month=month
    ).select_related("category")
    budgets_map = {b.category_id: b for b in budgets_qs}

    spent_list = (
        Expense.objects.filter(
            user=request.user,
            date__gte=month_start,
            date__lte=month_end,
            category_id__isnull=False,
        )
        .values("category_id")
        .annotate(spent=Sum("amount"))
    )
    spent_map = {r["category_id"]: r["spent"] for r in spent_list}

    items = []
    for cat in categories:
        spent = spent_map.get(cat.id) or Decimal("0")
        budget_obj = budgets_map.get(cat.id)
        items.append({
            "category": cat,
            "spent": spent,
            "budget": budget_obj.amount if budget_obj else None,
            "budget_obj": budget_obj,
        })

    return render(
        request,
        "categories/category_budget_list.html",
        {
            "items": items,
            "year": year,
            "month": month,
            "has_budgets": budgets_qs.exists(),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def category_budget_create(request):
    """Yangi turkum byudjeti yaratish."""
    form = CategoryBudgetForm(request.POST or None, user=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Turkum bo'yicha byudjet saqlandi.")
        return redirect("categories:budgets")
    return render(
        request,
        "categories/category_budget_form.html",
        {
            "form": form,
            "title": "Yangi turkum byudjeti",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def category_budget_edit(request, pk):
    """Mavjud turkum byudjetini tahrirlash."""
    budget = get_user_object_or_404(CategoryBudget, request.user, pk)
    form = CategoryBudgetForm(request.POST or None, instance=budget, user=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Turkum byudjeti yangilandi.")
        return redirect("categories:budgets")
    return render(
        request,
        "categories/category_budget_form.html",
        {
            "form": form,
            "budget": budget,
            "title": "Byudjetni tahrirlash",
        },
    )


@login_required
@require_http_methods(["POST"])
def category_budget_delete(request, pk):
    budget = get_user_object_or_404(CategoryBudget, request.user, pk)
    budget.delete()
    messages.success(request, "Turkum byudjeti o'chirildi.")
    return redirect("categories:budgets")
