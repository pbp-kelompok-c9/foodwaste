
from datetime import timedelta

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.http import require_POST

from food_waste_reporting.models import Report
from food_waste_management.models import ReportReview

from .models import DiscoveryReport, PickupClaim
from .forms import PickupProofForm
from .services import statistik_dashboard, expire_pending_claims


def discovery(request):

    keyword = request.GET.get("keyword", "")
    lokasi = request.GET.get("lokasi", "")
    acara = request.GET.get("acara", "")

    expire_pending_claims()

    laporan = DiscoveryReport.objects.cari(
        keyword=keyword,
        lokasi=lokasi,
        acara=acara
    ).filter(
        review__verification_status=ReportReview.Verification.ACCEPTED
    ).order_by("-created_at")

    sekarang = timezone.now()

    for makanan in laporan:

        klaim = PickupClaim.objects.filter(
            report=makanan,
            status__in=[
                PickupClaim.Status.PENDING,
                PickupClaim.Status.REVIEW,
                PickupClaim.Status.SUCCESS
            ]
        ).first()

        if klaim and klaim.status == PickupClaim.Status.SUCCESS:
            makanan.display_status = "NOT AVAILABLE"

        elif klaim and klaim.status == PickupClaim.Status.REVIEW:
            makanan.display_status = "MENUNGGU VERIFIKASI"

        elif makanan.best_before <= sekarang:
            makanan.display_status = "EXPIRED"

        elif klaim and klaim.status == PickupClaim.Status.PENDING:
            makanan.display_status = "DIPESAN"

        else:
            makanan.display_status = "AVAILABLE"

        makanan.can_claim = (
            makanan.display_status == "AVAILABLE"
        )

        makanan.own_pending_claim = (
            klaim is not None
            and klaim.status == PickupClaim.Status.PENDING
            and request.user.is_authenticated
            and klaim.user_id == request.user.pk
        )

    context = {
        "laporan": laporan,
        "keyword": keyword,
        "lokasi": lokasi,
        "acara": acara
    }

    return render(
        request,
        "discovery_dashboard/discovery.html",
        context
    )


def dashboard(request):

    data = statistik_dashboard()

    return render(
        request,
        "discovery_dashboard/dashboard.html",
        data
    )


@login_required
@require_POST
def start_pickup(request, report_id):

    try:
        with transaction.atomic():

            sekarang = timezone.now()

            laporan = get_object_or_404(
                Report.objects.select_for_update(),
                pk=report_id
            )

            review = getattr(laporan, "review", None)

            if laporan.best_before <= sekarang:
                return JsonResponse({
                    "error": "Makanan sudah kedaluwarsa."
                }, status=400)

            if (
                review is None
                or review.verification_status
                != ReportReview.Verification.ACCEPTED
            ):
                return JsonResponse({
                    "error": "Makanan belum disetujui admin."
                }, status=400)

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
                    return JsonResponse({
                        "error": "Makanan sudah tidak tersedia."
                    }, status=409)

                if klaim.status == PickupClaim.Status.REVIEW:
                    return JsonResponse({
                        "error": "Pengambilan makanan sedang diverifikasi admin."
                    }, status=409)

                if klaim.user_id != request.user.pk:
                    return JsonResponse({
                        "error": "Makanan sedang dipesan pengguna lain."
                    }, status=409)

            else:

                klaim = PickupClaim.objects.create(
                    report=laporan,
                    user=request.user,
                    status=PickupClaim.Status.PENDING,
                    created_at=sekarang,
                    expired_at=sekarang + timedelta(minutes=5)
                )

    except IntegrityError:
        return JsonResponse({
            "error": "Makanan sedang dipesan pengguna lain."
        }, status=409)

    return JsonResponse({
        "claim_id": klaim.pk,
        "status": klaim.status,
        "expired_at": klaim.expired_at.isoformat(),
        "server_now": timezone.now().isoformat(),
        "upload_url": reverse(
            "discovery_dashboard:upload_pickup",
            args=[klaim.pk]
        )
    })


@login_required
@require_POST
def upload_pickup(request, claim_id):

    with transaction.atomic():

        klaim = get_object_or_404(
            PickupClaim.objects.select_for_update(),
            pk=claim_id,
            user=request.user
        )

        if klaim.status != PickupClaim.Status.PENDING:
            return JsonResponse({
                "error": "Transaksi sudah tidak aktif."
            }, status=400)

        if klaim.is_expired():

            klaim.status = PickupClaim.Status.EXPIRED
            klaim.save(update_fields=["status"])

            return JsonResponse({
                "error": "Waktu pengambilan sudah habis."
            }, status=400)

        form = PickupProofForm(
            request.POST,
            request.FILES,
            instance=klaim
        )

        if not form.is_valid():
            return JsonResponse({
                "error": "Foto tidak valid atau terlalu besar.",
                "details": form.errors.get_json_data()
            }, status=400)

        klaim = form.save(commit=False)

        klaim.status = PickupClaim.Status.REVIEW
        klaim.uploaded_at = timezone.now()

        klaim.save()

    return JsonResponse({
        "success": True,
        "status": "REVIEW",
        "message": "Foto berhasil dikirim dan menunggu verifikasi admin."
    })
