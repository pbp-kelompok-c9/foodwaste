from django.contrib import messages
from django.shortcuts import redirect, render
from food_waste_reporting.forms import ReportForm
from django.contrib.auth.decorators import login_required 

def show_reports(request):
    context = {
        "title": "Food Waste Reporting",
        "form": ReportForm(),
    }
    return render(request, 'reports.html', context)

@login_required(login_url="authentication:login")
def create_report(request):
    form = ReportForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.created_by = request.user
        report.save()
        messages.success(request, "Laporan baru berhasil ditambahkan!")
        return redirect("main:show_reports")

    context = {
        "title": 'Food Waste Reporting',
        "form": form,
    }
    return render(request, "reports.html", context)
