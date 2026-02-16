from django.urls import path
from . import views

app_name = "categories"

urlpatterns = [
    path("categories/", views.category_list, name="list"),
    path("categories/new/", views.category_create, name="create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="delete"),
]
