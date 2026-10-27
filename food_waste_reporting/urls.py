from django.urls import path
from food_waste_reporting.views import show_reports, get_reports_json, create_report_ajax, view_report_detail, delete_report, edit_report

app_name = 'food_waste_reporting'

urlpatterns = [
    path('', show_reports, name='show_reports'),
    path('api/reports/', get_reports_json, name="get_reports_json"),
    path('reports/add-ajax/', create_report_ajax, name="create_report_ajax"),
    path('reports/<uuid:report_id>/view/', view_report_detail, name="view_report_detail"),
    path('reports/<uuid:report_id>/delete/', delete_report, name="delete_report"),
    path('reports/<uuid:report_id>/edit/', edit_report, name="edit_report"),
]