from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='main_landing.html'), name='main_landing'),
    path('management/', include('food_waste_management.urls')),
    path('reporting/', include('food_waste_reporting.urls')),
]