from rest_framework import serializers
from django.utils import timezone

from .models import DiscoveryReport, PickupClaim


class DiscoveryReportSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    can_claim = serializers.SerializerMethodField()

    class Meta:
        model = DiscoveryReport
        fields = [
            "id",
            "food_name",
            "food_portion",
            "best_before",
            "location",
            "event",
            "details",
            "picture",
            "created_at",
            "status",
            "can_claim",
        ]

    def get_status(self, obj):
        now = timezone.now()

        claims = obj.pickup_claims.filter(
            status__in=[
                PickupClaim.Status.PENDING,
                PickupClaim.Status.REVIEW,
                PickupClaim.Status.SUCCESS,
            ]
        )

        if claims.filter(
            status=PickupClaim.Status.SUCCESS
        ).exists():
            return "NOT AVAILABLE"

        if claims.filter(
            status=PickupClaim.Status.REVIEW
        ).exists():
            return "MENUNGGU VERIFIKASI"

        if obj.best_before <= now:
            return "EXPIRED"

        if claims.filter(
            status=PickupClaim.Status.PENDING,
            expired_at__gt=now,
        ).exists():
            return "DIPESAN"

        return "AVAILABLE"

    def get_can_claim(self, obj):
        return self.get_status(obj) == "AVAILABLE"


class PickupClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = PickupClaim
        fields = [
            "id",
            "report",
            "status",
            "created_at",
            "expired_at",
            "proof_photo",
            "uploaded_at",
            "completed_at",
        ]
        read_only_fields = fields
