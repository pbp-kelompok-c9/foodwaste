from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import PickupClaim


@admin.register(PickupClaim)
class PickupClaimAdmin(admin.ModelAdmin):

    list_display = (
        "report",
        "user",
        "status",
        "lihat_foto",
        "created_at",
        "uploaded_at"
    )

    list_filter = (
        "status",
        "created_at"
    )

    search_fields = (
        "report__food_name",
    )

    readonly_fields = (
        "report",
        "user",
        "status",
        "created_at",
        "expired_at",
        "proof_photo",
        "lihat_foto",
        "uploaded_at",
        "completed_at"
    )

    actions = [
        "setujui_pengambilan",
        "tolak_pengambilan"
    ]

    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    @admin.display(description="Foto Bukti")
    def lihat_foto(self, obj):

        if obj.proof_photo:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">Lihat Foto</a>',
                obj.proof_photo.url
            )

        return "-"

    @admin.action(description="Setujui pengambilan makanan")
    def setujui_pengambilan(self, request, queryset):

        jumlah = queryset.filter(
            status=PickupClaim.Status.REVIEW
        ).update(
            status=PickupClaim.Status.SUCCESS,
            completed_at=timezone.now()
        )

        self.message_user(
            request,
            f"{jumlah} pengambilan berhasil disetujui."
        )

    @admin.action(description="Tolak pengambilan makanan")
    def tolak_pengambilan(self, request, queryset):

        jumlah = queryset.filter(
            status=PickupClaim.Status.REVIEW
        ).update(
            status=PickupClaim.Status.REJECTED,
            completed_at=None
        )

        self.message_user(
            request,
            f"{jumlah} pengambilan berhasil ditolak."
        )
