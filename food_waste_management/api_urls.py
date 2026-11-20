
from django.urls import path

from . import api_views

app_name = "food_waste_management_api"

urlpatterns = [
    path(
        "reviews/",
        api_views.ReportReviewListAPIView.as_view(),
        name="review-list",
    ),
    path(
        "reviews/<uuid:report_id>/",
        api_views.ReportReviewDetailAPIView.as_view(),
        name="review-detail",
    ),
    path(
        "reviews/<uuid:report_id>/accept/",
        api_views.AcceptReportAPIView.as_view(),
        name="accept-report",
    ),
    path(
        "reviews/<uuid:report_id>/reject/",
        api_views.RejectReportAPIView.as_view(),
        name="reject-report",
    ),
    path(
        "reviews/<uuid:report_id>/handling/",
        api_views.UpdateHandlingAPIView.as_view(),
        name="update-handling",
    ),
    path(
        "reviews/<uuid:report_id>/follow-up/",
        api_views.UpdateFollowUpAPIView.as_view(),
        name="update-follow-up",
    ),
]
