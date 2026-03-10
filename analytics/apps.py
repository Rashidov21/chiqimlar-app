from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "analytics"
    verbose_name = "Tahlil"

    def ready(self):
        import analytics.signals  # noqa: F401 — achievement trigger post_save(Expense)
