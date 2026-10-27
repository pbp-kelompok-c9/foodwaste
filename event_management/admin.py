from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "event_date", "location", "created_by")
    list_filter = ("event_date",)
    search_fields = ("name", "location", "created_by__username")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("created_by",)
