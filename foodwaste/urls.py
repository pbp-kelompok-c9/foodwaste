from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='main_landing.html'), name='main_landing'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('', include('authentication.urls')),
    path('management/', include('food_waste_management.urls')),
    path('events/', include('event_management.urls')),
    path('reporting/', include('food_waste_reporting.urls')),
]

if settings.GOOGLE_LOGIN_ENABLED:
    urlpatterns += [path('accounts/', include('allauth.urls'))]
