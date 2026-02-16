from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login_alt"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
]
