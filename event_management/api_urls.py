from django.urls import path

from .api_views import EventDetailAPIView, EventListCreateAPIView

app_name = "event_management_api"

urlpatterns = [
    path("", EventListCreateAPIView.as_view(), name="list"),
    path("<int:pk>/", EventDetailAPIView.as_view(), name="detail"),
]
