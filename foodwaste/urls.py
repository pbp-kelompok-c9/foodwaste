from django.conf import settings
from django.urls import path, include
from django.views.generic import TemplateView

if settings.CHECKPOINT_ONLY:
    from django.views.debug import default_urlconf

    urlpatterns = [path('', default_urlconf, name='main_landing')]
else:
    from django.contrib import admin

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('', TemplateView.as_view(template_name='main_landing.html'), name='main_landing'),
        path('', include('authentication.urls')),
        path('management/', include('food_waste_management.urls')),
        path('reporting/', include('food_waste_reporting.urls')),
    ]

    if settings.GOOGLE_LOGIN_ENABLED:
        urlpatterns += [path('accounts/', include('allauth.urls'))]
