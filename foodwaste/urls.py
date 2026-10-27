
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from discovery_dashboard.views import discovery


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', discovery, name='main_landing'),

    path(
        'privacy/',
        TemplateView.as_view(template_name='privacy.html'),
        name='privacy'
    ),

    path(
        'terms/',
        TemplateView.as_view(template_name='terms.html'),
        name='terms'
    ),

    path('', include('authentication.urls')),
    path('management/', include('food_waste_management.urls')),
    path('events/', include('event_management.urls')),
    path('reporting/', include('food_waste_reporting.urls')),

    path('', include('discovery_dashboard.urls')),
]


if settings.GOOGLE_LOGIN_ENABLED:
    urlpatterns += [
        path('accounts/', include('allauth.urls'))
    ]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
