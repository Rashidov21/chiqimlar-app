from django.contrib import admin

from .models import RequiredChannel


@admin.register(RequiredChannel)
class RequiredChannelAdmin(admin.ModelAdmin):
    list_display = ["name", "username", "channel_id", "is_active", "is_mandatory", "created_at"]
    list_filter = ["is_active", "is_mandatory"]
    search_fields = ["name", "username", "channel_id"]
    readonly_fields = ["created_at"]

