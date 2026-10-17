from django.contrib import messages
from django.shortcuts import redirect, render
from food_waste_reporting.forms import ReportForm

def show_reports(request):
    context = {
        "title": "Food Waste Reporting",
        "form": ReportForm(),
    }
    return render(request, 'reports.html', context)

def create_report(request):
    form = ReportForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Laporan baru berhasil ditambahkan!")
        return redirect("main:show_reports")

    context = {
        "title": 'Food Waste Reporting',
        "form": form,
    }
    return render(request, "reports.html", context)
