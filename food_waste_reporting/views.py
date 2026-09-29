from django.shortcuts import render

def show_reports(request):
    context = {
        'title': 'Food Waste Reporting',
    }
    return render(request, 'reports_landing.html', context)
