from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "emoji", "user", "order"]
    list_filter = ["user"]
    search_fields = ["name"]
