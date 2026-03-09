from django.urls import path
from . import views

app_name = "expenses"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("add/", views.expense_add, name="add"),
    path("expenses/", views.expense_list, name="list"),
    path("expenses/<int:pk>/edit/", views.expense_edit, name="edit"),
    path("expenses/<int:pk>/delete/", views.expense_delete, name="delete"),
    path("settings/", views.settings_view, name="settings"),
    path("export/", views.export_view, name="export"),
    path("export/excel-to-telegram/", views.export_excel_to_telegram, name="export_excel_to_telegram"),
]
