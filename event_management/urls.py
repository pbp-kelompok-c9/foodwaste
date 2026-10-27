
from django.urls import path
from . import views

app_name = "event_management"

urlpatterns = [
    path("", views.main, name="main"),
    path("create/", views.event_create, name="create"),
    path("<int:event_id>/", views.event_detail, name="detail"),
    path("<int:event_id>/edit/", views.event_update, name="edit"),
    path("<int:event_id>/delete/", views.event_delete, name="delete"),
]
