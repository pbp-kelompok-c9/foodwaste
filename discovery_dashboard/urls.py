from django.urls import path
from . import views

app_name = "discovery_dashboard"

urlpatterns = [
    path("", views.discovery, name="discovery"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
