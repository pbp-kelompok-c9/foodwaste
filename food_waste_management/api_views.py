
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ReportReview, ReviewTransitionError
from .serializers import (
    ReportReviewSerializer,
    RejectReportSerializer,
    HandlingUpdateSerializer,
    FollowUpUpdateSerializer,
)


def review_queryset():
    return ReportReview.objects.select_related(
        "report",
        "report__reported_by",
        "report__related_event",
        "reviewed_by",
    ).prefetch_related(
        "report__pickup_claims__user"
    )


class ReportReviewListAPIView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ReportReviewSerializer
    queryset = review_queryset()


class ReportReviewDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ReportReviewSerializer
    queryset = review_queryset()
    lookup_field = "report_id"
    lookup_url_kwarg = "report_id"


class ReportReviewActionAPIView(APIView):
    permission_classes = [IsAdminUser]

    def update_review(self, request, report_id, action, message):
        with transaction.atomic():
            review = get_object_or_404(
                ReportReview.objects.select_for_update(),
                report_id=report_id,
            )

            try:
                action(review)
            except ReviewTransitionError as exc:
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            review.refresh_from_db()

            serializer = ReportReviewSerializer(
                review,
                context={"request": request},
            )

            return Response({
                "message": message,
                "data": serializer.data,
            })


class AcceptReportAPIView(ReportReviewActionAPIView):
    def post(self, request, report_id):
        return self.update_review(
            request,
            report_id,
            lambda review: review.accept(request.user),
            "Laporan berhasil diterima.",
        )


class RejectReportAPIView(ReportReviewActionAPIView):
    def post(self, request, report_id):
        serializer = RejectReportSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = serializer.validated_data["reason"]

        return self.update_review(
            request,
            report_id,
            lambda review: review.reject(request.user, reason),
            "Laporan berhasil ditolak.",
        )


class UpdateHandlingAPIView(ReportReviewActionAPIView):
    def post(self, request, report_id):
        serializer = HandlingUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_status = serializer.validated_data["handling_status"]

        return self.update_review(
            request,
            report_id,
            lambda review: review.set_handling(new_status),
            "Status penanganan berhasil diperbarui.",
        )


class UpdateFollowUpAPIView(ReportReviewActionAPIView):
    def post(self, request, report_id):
        serializer = FollowUpUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        follow_up = serializer.validated_data["follow_up"]

        return self.update_review(
            request,
            report_id,
            lambda review: review.set_follow_up(follow_up),
            "Tindak lanjut berhasil diperbarui.",
        )
