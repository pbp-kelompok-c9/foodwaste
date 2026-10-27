from django.urls import path
from . import views

app_name = "discovery_dashboard"

urlpatterns = [
    path(
        "discovery/",
        views.discovery,
        name="discovery"
    ),

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    path(
        "pickup/<uuid:report_id>/start/",
        views.start_pickup,
        name="start_pickup"
    ),

    path(
        "pickup/upload/<int:claim_id>/",
        views.upload_pickup,
        name="upload_pickup"
    ),
]
