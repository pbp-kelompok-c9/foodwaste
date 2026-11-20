from django.urls import path
from . import views
from .api_views import (
    DashboardAPIView,
    DiscoveryAPIView,
    StartPickupAPIView,
    UploadPickupAPIView,
)

app_name = "discovery_dashboard"

urlpatterns = [
    path("", views.discovery, name="discovery"),
    path("discovery/", views.discovery, name="discovery_page"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("pickup/<uuid:report_id>/start/", views.start_pickup, name="start_pickup"),
    path("pickup/upload/<int:claim_id>/", views.upload_pickup, name="upload_pickup"),
    path("api/dashboard/", DashboardAPIView.as_view(), name="api_dashboard"),
    path("api/discovery/", DiscoveryAPIView.as_view(), name="api_discovery"),
    path("api/discovery/pickup/<uuid:report_id>/start/", StartPickupAPIView.as_view(), name="api_start_pickup"),
    path("api/discovery/pickup/<int:claim_id>/upload/", UploadPickupAPIView.as_view(), name="api_upload_pickup"),
]
