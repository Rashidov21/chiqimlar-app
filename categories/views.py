from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import Category
from .forms import CategoryForm


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
    return render(request, "categories/category_list.html", {"categories": categories})


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
    category = get_object_or_404(Category, pk=pk, user=request.user)
    form = CategoryForm(request.POST or None, instance=category, user=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Turkum yangilandi.")
        return redirect("categories:list")
    return render(request, "categories/category_form.html", {"form": form, "category": category, "title": "Turkumni tahrirlash"})


@login_required
@require_http_methods(["POST"])
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    category.delete()
    messages.success(request, "Turkum o'chirildi.")
    return redirect("categories:list")
