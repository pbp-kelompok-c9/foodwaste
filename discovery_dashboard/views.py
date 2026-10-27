
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


# ==========================================
# DISCOVERY / BERANDA
# ==========================================

def discovery(request):

    keyword = request.GET.get("keyword", "")
    lokasi = request.GET.get("lokasi", "")
    acara = request.GET.get("acara", "")

    # Perbarui reservasi yang sudah kedaluwarsa
    expire_pending_claims()

    laporan = DiscoveryReport.objects.cari(
        keyword=keyword,
        lokasi=lokasi,
        acara=acara
    ).order_by("-created_at")

    sekarang = timezone.now()

    for makanan in laporan:

        review = getattr(makanan, "review", None)

        klaim = PickupClaim.objects.filter(
            report=makanan,
            status__in=[
                PickupClaim.Status.PENDING,
                PickupClaim.Status.SUCCESS
            ]
        ).first()

        disetujui = (
            review is not None
            and review.verification_status
            == ReportReview.Verification.ACCEPTED
        )

        # Makanan sudah diambil
        if klaim and klaim.status == PickupClaim.Status.SUCCESS:
            makanan.display_status = "SUDAH DIAMBIL"

        # Makanan sudah melewati best before
        elif makanan.best_before <= sekarang:
            makanan.display_status = "EXPIRED"

        # Laporan belum disetujui
        elif not disetujui:
            makanan.display_status = "TIDAK TERSEDIA"

        # Makanan sedang dipesan
        elif klaim:
            makanan.display_status = "DIPESAN"

        # Makanan tersedia
        else:
            makanan.display_status = "AVAILABLE"

        # Menentukan apakah tombol Ambil bisa digunakan
        makanan.can_claim = (
            makanan.display_status == "AVAILABLE"
        )

        # Pengguna yang sedang memesan bisa melanjutkan
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


# ==========================================
# DASHBOARD
# ==========================================

def dashboard(request):

    data = statistik_dashboard()

    return render(
        request,
        "discovery_dashboard/dashboard.html",
        data
    )


# ==========================================
# MULAI PENGAMBILAN MAKANAN
# ==========================================

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

            # Periksa apakah makanan masih tersedia
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
                    "error": "Makanan belum disetujui."
                }, status=400)

            # Akhiri klaim lama yang sudah lewat 5 menit
            PickupClaim.objects.filter(
                report=laporan,
                status=PickupClaim.Status.PENDING,
                expired_at__lte=sekarang
            ).update(
                status=PickupClaim.Status.EXPIRED
            )

            # Cek apakah makanan sedang dipesan atau diambil
            klaim = PickupClaim.objects.filter(
                report=laporan,
                status__in=[
                    PickupClaim.Status.PENDING,
                    PickupClaim.Status.SUCCESS
                ]
            ).first()

            if klaim:

                if klaim.status == PickupClaim.Status.SUCCESS:
                    return JsonResponse({
                        "error": "Makanan sudah diambil."
                    }, status=409)

                if klaim.user_id != request.user.pk:
                    return JsonResponse({
                        "error": "Makanan sedang dipesan pengguna lain."
                    }, status=409)

            else:

                # Buat transaksi dengan waktu 5 menit
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


# ==========================================
# UPLOAD FOTO BUKTI PENGAMBILAN
# ==========================================

@login_required
@require_POST
def upload_pickup(request, claim_id):

    with transaction.atomic():

        klaim = get_object_or_404(
            PickupClaim.objects.select_for_update(),
            pk=claim_id,
            user=request.user
        )

        # Periksa status transaksi
        if klaim.status != PickupClaim.Status.PENDING:
            return JsonResponse({
                "error": "Transaksi sudah tidak aktif."
            }, status=400)

        # Periksa batas waktu
        if klaim.is_expired():

            klaim.status = PickupClaim.Status.EXPIRED
            klaim.save(update_fields=["status"])

            return JsonResponse({
                "error": "Waktu pengambilan sudah habis."
            }, status=400)

        # Validasi foto
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

        # Simpan foto dan selesaikan transaksi
        klaim = form.save(commit=False)

        klaim.status = PickupClaim.Status.SUCCESS
        klaim.completed_at = timezone.now()

        klaim.save()

    return JsonResponse({
        "success": True,
        "status": "SUCCESS",
        "message": "Foto berhasil dikirim! Makanan sudah diambil."
    })
