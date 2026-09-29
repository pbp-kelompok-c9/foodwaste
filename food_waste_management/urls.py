from django.urls import path
from food_waste_management.views import show_management

app_name = 'food_waste_management'

urlpatterns = [
    path('', show_management, name='show_management'),
]