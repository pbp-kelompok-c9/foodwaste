from django.shortcuts import render
from .models import DiscoveryReport
from .services import statistik_dashboard


def discovery(request):
    keyword = request.GET.get("keyword", "")
    lokasi = request.GET.get("lokasi", "")
    acara = request.GET.get("acara", "")

    laporan = DiscoveryReport.objects.cari(
        keyword=keyword,
        lokasi=lokasi,
        acara=acara
    ).order_by("-created_at")

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
