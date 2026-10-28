from datetime import timezone

from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from food_waste_reporting.models import Report
from food_waste_reporting.forms import ReportForm
from django.contrib.auth.decorators import login_required 
from django.views.decorators.http import require_POST, require_http_methods

@login_required(login_url="authentication:login")
def show_reports(request):
    context = {
        "title": "Food Waste Reporting",
        "form": ReportForm(),
    }
    return render(request, 'reports.html', context)

@login_required(login_url="authentication:login")
def get_reports_json(request):
    reports = Report.objects.filter(reported_by=request.user).select_related("related_event")

    name_query = request.GET.get("name", "").strip()

    if name_query:
        reports = reports.filter(food_name__icontains=name_query)

    data = [
        {
            "id": report.pk,
            "picture": report.image.url if report.picture else "",
            "food_name": report.food_name,
            "food_portion": report.food_portion,
            "best_before": report.best_before.strftime("%d/%m/%Y"),
            "location": report.location,
            "event": report.event_label,
            "related_event_id": report.related_event_id,
        }
        for report in reports
    ]

    return JsonResponse({"reports": data})

@login_required(login_url="authentication:login")
@require_POST
def create_report_ajax(request):
    form = ReportForm(request.POST, request.FILES)
    if form.is_valid():
        report = form.save(commit=False)
        report.reported_by = request.user
        report.save()
        return JsonResponse(
            {"message": "Laporan berhasil dibuat!", "pk": str(report.id)},
            status=201,
        )
    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)

def view_report_detail(request, report_id):
    report = get_object_or_404(Report.objects.select_related("related_event"), pk=report_id)
    return render(request, "components/report_detail_modal.html", {"report": report})

@require_POST
def delete_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    report.delete()
    return JsonResponse({"message": "Laporan berhasil dhapus!"})

@require_http_methods(["GET", "POST"])
def edit_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)

    if request.method == "POST":
        form = ReportForm(request.POST, request.FILES, instance=report)
        if form.is_valid():
            form.save()
            return JsonResponse({"message": "Laporan berhasil diedit!"})
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)

    data = {
        "food_name": report.food_name,
        "food_portion": report.food_portion,
        "best_before": report.best_before.strftime("%d/%m/%Y"),
        "location": report.location,
        "event": report.event_label,
        "pickup_option": report.pickup_option,
        "details": report.details,
    }
    return JsonResponse(data)
    