from datetime import timezone

from django.contrib import messages
from django.shortcuts import redirect, render
from django.http import JsonResponse
from food_waste_reporting.models import Report
from food_waste_reporting.forms import ReportForm
from django.contrib.auth.decorators import login_required 
from django.views.decorators.http import require_POST

def show_reports(request):
    context = {
        "title": "Food Waste Reporting",
        "form": ReportForm(),
    }
    return render(request, 'reports.html', context)

def get_reports_json(request):
    reports = Report.objects.filter(reported_by=request.user)

    name_query = request.GET.get("name", "").strip()

    if name_query:
        reports = reports.filter(food_name__icontains=name_query)

    data = [
        {
            "id": report.pk,
            "food_name": report.food_name,
            "portion": report.food_portion,
            "best_before": report.best_before,
            "location": report.location,
            "event": report.event,
        }
        for report in reports
    ]

    return JsonResponse({"reports": data})

@login_required(login_url="authentication:login")
@require_POST
def create_report_ajax(request):
    form = ReportForm(request.POST)
    if form.is_valid():
        report = form.save(commit=False)
        report.reported_by = request.user
        report.save()
        return JsonResponse(
            {"message": "Laporan berhasil dibuat!", "pk": str(report.id)},
            status=201,
        )
    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)