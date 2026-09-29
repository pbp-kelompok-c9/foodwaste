from django.urls import path
from food_waste_reporting.views import show_reports

app_name = 'food_waste_reporting'

urlpatterns = [
    path('', show_reports, name='show_reports'),
]