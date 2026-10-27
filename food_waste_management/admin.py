from django.contrib import admin

from food_waste_management.models import ReportReview


@admin.register(ReportReview)
class ReportReviewAdmin(admin.ModelAdmin):
    list_display = ("report", "verification_status", "handling_status", "follow_up",
                    "reviewed_by", "reviewed_at")
    list_filter = ("verification_status", "handling_status", "follow_up")
    search_fields = ("report__food_name", "report__location", "report__event", "report__related_event__name")
    list_select_related = ("report", "report__related_event", "reviewed_by")
    readonly_fields = ("report", "reviewed_by", "reviewed_at", "created_at", "updated_at")
