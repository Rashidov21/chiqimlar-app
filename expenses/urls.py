from django.urls import path
from . import views

app_name = "expenses"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("onboarding/", views.onboarding_view, name="onboarding"),
    path("goals/", views.saving_goal_list, name="saving_goal_list"),
    path("goals/add/", views.saving_goal_create, name="saving_goal_create"),
    path("goals/<int:pk>/edit/", views.saving_goal_edit, name="saving_goal_edit"),
    path("recurring/", views.recurring_list, name="recurring_list"),
    path("recurring/add/", views.recurring_create, name="recurring_create"),
    path("recurring/<int:pk>/edit/", views.recurring_edit, name="recurring_edit"),
    path("recurring/<int:pk>/delete/", views.recurring_delete, name="recurring_delete"),
    path("recurring/<int:pk>/mark-paid/", views.recurring_mark_paid, name="recurring_mark_paid"),
    path("debts/", views.debt_list, name="debt_list"),
    path("debts/add/", views.debt_create, name="debt_create"),
    path("debts/<int:pk>/edit/", views.debt_edit, name="debt_edit"),
    path("debts/<int:pk>/delete/", views.debt_delete, name="debt_delete"),
    path("add/", views.expense_add, name="add"),
    path("expenses/", views.expense_list, name="list"),
    path("expenses/<int:pk>/edit/", views.expense_edit, name="edit"),
    path("expenses/<int:pk>/delete/", views.expense_delete, name="delete"),
    path("settings/", views.settings_view, name="settings"),
    path("settings/donation-moderation/", views.donation_moderation_view, name="donation_moderation"),
    path(
        "settings/donation-moderation/<int:donation_id>/photo/",
        views.donation_moderation_photo,
        name="donation_moderation_photo",
    ),
    path("export/", views.export_view, name="export"),
    path("export/excel-to-telegram/", views.export_excel_to_telegram, name="export_excel_to_telegram"),
]
