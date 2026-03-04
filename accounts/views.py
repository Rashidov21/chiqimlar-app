"""
Hisoblar - Login, ro'yxatdan o'tish, chiqish, Telegram Mini App auth.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse

from .services import verify_code_and_login, get_or_create_user_by_telegram
from .forms import LoginForm, RegisterForm
from .telegram_auth import validate_telegram_init_data


@require_http_methods(["GET", "POST", "HEAD"])
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


@require_http_methods(["GET", "POST", "HEAD"])
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


@csrf_exempt
@require_POST
def telegram_webapp_auth(request):
    """
    Telegram Mini App: initData orqali avtomatik login.
    POST: init_data=<Telegram.WebApp.initData>
    """
    init_data = request.POST.get("init_data", "").strip()
    if not init_data and request.body:
        try:
            import json as _json
            data = _json.loads(request.body)
            init_data = data.get("init_data", "")
        except Exception:
            pass
    user_data = validate_telegram_init_data(init_data)
    if not user_data:
        return JsonResponse({"ok": False, "error": "invalid_init_data"}, status=400)
    telegram_id = user_data.get("id")
    if not telegram_id:
        return JsonResponse({"ok": False, "error": "no_user"}, status=400)
    user = get_or_create_user_by_telegram(
        telegram_id=telegram_id,
        first_name=user_data.get("first_name", ""),
    )
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse({"ok": True, "redirect": "/"})
