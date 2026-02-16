from django.urls import path
from . import views

app_name = "analytics"

urlpatterns = [
    path("statistics/", views.statistics_view, name="statistics"),
    path("api/chart/daily/", views.chart_data_daily, name="chart_daily"),
    path("api/chart/categories/", views.chart_data_categories, name="chart_categories"),
]
