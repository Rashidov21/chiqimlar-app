"""
Hisoblar - Login, ro'yxatdan o'tish, chiqish.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from .services import verify_code_and_login
from .forms import LoginForm, RegisterForm


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("expenses:dashboard")
    form = LoginForm(request.POST or None)
    if form.is_valid():
        user, msg = verify_code_and_login(form.cleaned_data["code"], request)
        if user:
            messages.success(request, msg)
            return redirect("expenses:dashboard")
        messages.error(request, msg)
    return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("expenses:dashboard")
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password1"])
        user.save()
        from django.contrib.auth import login
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Hisobingiz yaratildi. Endi Telegram orqali kod olishingiz mumkin.")
        return redirect("expenses:dashboard")
    return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["POST"])
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Siz tizimdan chiqdingiz.")
    return redirect("accounts:login")


@login_required
def settings_view(request):
    return redirect("expenses:settings")
