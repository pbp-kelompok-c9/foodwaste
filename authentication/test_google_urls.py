"""Test URL configuration enables OAuth routes without real credentials."""
from django.urls import include, path
from foodwaste.urls import urlpatterns as project_patterns

urlpatterns = list(project_patterns) + [path('accounts/', include('allauth.urls'))]
