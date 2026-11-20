from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from food_waste_management.models import ReportReview

from .models import DiscoveryReport
from .serializers import DiscoveryReportSerializer
from .services import statistik_dashboard, expire_pending_claims

from datetime import timedelta

from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse

from rest_framework import status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from food_waste_reporting.models import Report

from .models import PickupClaim
from .forms import PickupProofForm


class DashboardAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        data = statistik_dashboard()
        return Response(data)


class DiscoveryAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        expire_pending_claims()

        keyword = request.query_params.get("keyword", "")
        lokasi = request.query_params.get("lokasi", "")
        acara = request.query_params.get("acara", "")

        laporan_disetujui = ReportReview.objects.filter(
            verification_status=ReportReview.Verification.ACCEPTED
        ).values_list("report_id", flat=True)

        laporan = DiscoveryReport.objects.cari(
            keyword=keyword,
            lokasi=lokasi,
            acara=acara
        ).filter(
            pk__in=laporan_disetujui
        ).prefetch_related("pickup_claims")

        serializer = DiscoveryReportSerializer(
            laporan,
            many=True
        )

        return Response({
            "results": serializer.data
        })

class StartPickupAPIView(APIView):
    authentication_classes = [
        TokenAuthentication,
        SessionAuthentication
    ]
    permission_classes = [IsAuthenticated]

    def post(self, request, report_id):
        try:
            with transaction.atomic():
                sekarang = timezone.now()

                laporan = get_object_or_404(
                    Report.objects.select_for_update(),
                    pk=report_id
                )

                review = getattr(laporan, "review", None)

                if laporan.best_before <= sekarang:
                    return Response({
                        "error": "Makanan sudah kedaluwarsa."
                    }, status=status.HTTP_400_BAD_REQUEST)

                if (
                    review is None
                    or review.verification_status
                    != ReportReview.Verification.ACCEPTED
                ):
                    return Response({
                        "error": "Makanan belum disetujui admin."
                    }, status=status.HTTP_400_BAD_REQUEST)

                PickupClaim.objects.filter(
                    report=laporan,
                    status=PickupClaim.Status.PENDING,
                    expired_at__lte=sekarang
                ).update(
                    status=PickupClaim.Status.EXPIRED
                )

                klaim = PickupClaim.objects.filter(
                    report=laporan,
                    status__in=[
                        PickupClaim.Status.PENDING,
                        PickupClaim.Status.REVIEW,
                        PickupClaim.Status.SUCCESS
                    ]
                ).first()

                if klaim:
                    if klaim.status == PickupClaim.Status.SUCCESS:
                        return Response({
                            "error": "Makanan sudah tidak tersedia."
                        }, status=status.HTTP_409_CONFLICT)

                    if klaim.status == PickupClaim.Status.REVIEW:
                        return Response({
                            "error": "Pengambilan sedang diverifikasi admin."
                        }, status=status.HTTP_409_CONFLICT)

                    if klaim.user_id != request.user.pk:
                        return Response({
                            "error": "Makanan sedang dipesan pengguna lain."
                        }, status=status.HTTP_409_CONFLICT)

                else:
                    klaim = PickupClaim.objects.create(
                        report=laporan,
                        user=request.user,
                        status=PickupClaim.Status.PENDING,
                        created_at=sekarang,
                        expired_at=sekarang + timedelta(minutes=5)
                    )

        except IntegrityError:
            return Response({
                "error": "Makanan sedang dipesan pengguna lain."
            }, status=status.HTTP_409_CONFLICT)

        return Response({
            "claim_id": klaim.pk,
            "status": klaim.status,
            "expired_at": klaim.expired_at.isoformat(),
            "server_now": timezone.now().isoformat(),
            "upload_url": reverse(
                "discovery_dashboard:api_upload_pickup",
                args=[klaim.pk]
            )
        })


class UploadPickupAPIView(APIView):
    authentication_classes = [
        TokenAuthentication,
        SessionAuthentication
    ]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, claim_id):
        with transaction.atomic():
            klaim = get_object_or_404(
                PickupClaim.objects.select_for_update(),
                pk=claim_id,
                user=request.user
            )

            if klaim.status != PickupClaim.Status.PENDING:
                return Response({
                    "error": "Transaksi sudah tidak aktif."
                }, status=status.HTTP_400_BAD_REQUEST)

            if klaim.is_expired():
                klaim.status = PickupClaim.Status.EXPIRED
                klaim.save(update_fields=["status"])

                return Response({
                    "error": "Waktu pengambilan sudah habis."
                }, status=status.HTTP_400_BAD_REQUEST)

            form = PickupProofForm(
                request.data,
                request.FILES,
                instance=klaim
            )

            if not form.is_valid():
                return Response({
                    "error": "Foto tidak valid atau terlalu besar.",
                    "details": form.errors.get_json_data()
                }, status=status.HTTP_400_BAD_REQUEST)

            klaim = form.save(commit=False)
            klaim.status = PickupClaim.Status.REVIEW
            klaim.uploaded_at = timezone.now()
            klaim.save()

        return Response({
            "success": True,
            "status": "REVIEW",
            "message": "Foto berhasil dikirim dan menunggu verifikasi admin."
        })
