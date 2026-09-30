from django.shortcuts import render


def main(request):
    return render(request, 'event_management/main.html')
