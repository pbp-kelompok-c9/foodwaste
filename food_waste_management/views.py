from django.shortcuts import render

def show_management(request):
    context = {
        'title': 'Food Waste Management',
    }
    return render(request, 'management_landing.html', context)