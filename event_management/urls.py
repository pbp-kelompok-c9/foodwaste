from django.urls import path
from . import views

app_name = 'event_management'
urlpatterns = [path('', views.main, name='main')]
