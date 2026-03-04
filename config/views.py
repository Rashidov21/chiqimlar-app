"""
Chiqimlar - Statik sahifalar: 404, 500, Maxfiylik, Yordam.
"""
from django.shortcuts import render
from django.views.defaults import page_not_found, server_error


def custom_404(request, exception=None):
    """Maxsus 404 sahifa."""
    return render(request, "404.html", status=404)


def custom_500(request):
    """Maxsus 500 sahifa."""
    return render(request, "500.html", status=500)


def privacy_view(request):
    """Maxfiylik siyosati sahifasi."""
    return render(request, "pages/privacy.html")


def help_view(request):
    """Yordam sahifasi."""
    return render(request, "pages/help.html")
