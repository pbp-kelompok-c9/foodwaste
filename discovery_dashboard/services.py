from django.db.models import Count, Sum
from food_waste_reporting.models import Report
from food_waste_management.models import ReportReview


def statistik_dashboard():
    total_laporan = Report.objects.count()

    total_porsi = Report.objects.aggregate(
        total=Sum("food_portion")
    )["total"] or 0

    status_verifikasi = ReportReview.objects.values(
        "verification_status"
    ).annotate(jumlah=Count("id"))

    status_penanganan = ReportReview.objects.values(
        "handling_status"
    ).annotate(jumlah=Count("id"))

    tindak_lanjut = ReportReview.objects.values(
        "follow_up"
    ).annotate(jumlah=Count("id"))

    return {
        "total_laporan": total_laporan,
        "total_porsi": total_porsi,
        "status_verifikasi": list(status_verifikasi),
        "status_penanganan": list(status_penanganan),
        "tindak_lanjut": list(tindak_lanjut),
    }
