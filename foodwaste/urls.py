"""Checkpoint 1: replace the root route when the application is implemented."""
from django.conf import settings
from django.urls import path
from django.views.debug import default_urlconf

urlpatterns = [
    # Explicitly show Django's bundled rocket page, including with DEBUG=False.
    path("", default_urlconf, name="checkpoint-rocket"),

]

if not settings.CHECKPOINT_ONLY:
    from django.contrib import admin
    urlpatterns.append(path("admin/", admin.site.urls))
