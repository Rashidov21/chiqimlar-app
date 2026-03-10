from django.urls import path
from . import views

app_name = "categories"

urlpatterns = [
    path("categories/", views.category_list, name="list"),
    path("categories/new/", views.category_create, name="create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="delete"),
    path("budgets/", views.category_budget_list, name="budgets"),
    path("budgets/new/", views.category_budget_create, name="budget_create"),
    path("budgets/<int:pk>/edit/", views.category_budget_edit, name="budget_edit"),
    path("budgets/<int:pk>/delete/", views.category_budget_delete, name="budget_delete"),
]
