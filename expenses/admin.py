from django.contrib import admin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["user", "category", "amount", "date", "created_at"]
    list_filter = ["date", "user"]
    search_fields = ["note", "amount"]
    date_hierarchy = "date"
