from django.urls import path
from food_waste_reporting.views import show_reports, get_reports_json, create_report_ajax

app_name = 'food_waste_reporting'

urlpatterns = [
    path('', show_reports, name='show_reports'),
    path('api/reports/', get_reports_json, name="get_reports_json"),
    path('reports/add-ajax/', create_report_ajax, name="create_report_ajax"),
]