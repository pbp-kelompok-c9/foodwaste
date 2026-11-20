
from rest_framework import serializers
from food_waste_reporting.models import Report
from discovery_dashboard.models import PickupClaim
from .models import ReportReview


class ReportSerializer(serializers.ModelSerializer):
    reported_by = serializers.StringRelatedField(read_only=True)
    event_label = serializers.CharField(read_only=True)
    picture = serializers.ImageField(read_only=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "reported_by",
            "food_name",
            "food_portion",
            "best_before",
            "location",
            "event",
            "related_event",
            "event_label",
            "pickup_option",
            "details",
            "picture",
            "created_at",
        ]
        read_only_fields = fields


class PickupClaimSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True
    )
    proof_photo = serializers.ImageField(read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = PickupClaim
        fields = [
            "id",
            "report",
            "user",
            "status",
            "status_display",
            "created_at",
            "expired_at",
            "proof_photo",
            "uploaded_at",
            "completed_at",
            "is_expired",
        ]
        read_only_fields = fields

    def get_is_expired(self, obj):
        return obj.is_expired()


class ReportReviewSerializer(serializers.ModelSerializer):
    report = ReportSerializer(read_only=True)
    report_id = serializers.UUIDField(read_only=True)
    reviewed_by = serializers.StringRelatedField(
        read_only=True,
        allow_null=True
    )
    pickup_claims = PickupClaimSerializer(
        source="report.pickup_claims",
        many=True,
        read_only=True
    )
    verification_status_display = serializers.CharField(
        source="get_verification_status_display",
        read_only=True
    )
    handling_status_display = serializers.CharField(
        source="get_handling_status_display",
        read_only=True
    )
    follow_up_display = serializers.CharField(
        source="get_follow_up_display",
        read_only=True
    )
    is_pending = serializers.BooleanField(read_only=True)
    is_accepted = serializers.BooleanField(read_only=True)
    is_rejected = serializers.BooleanField(read_only=True)
    next_handling = serializers.CharField(
        read_only=True,
        allow_null=True
    )
    next_handling_label = serializers.CharField(read_only=True)
    can_set_follow_up = serializers.BooleanField(read_only=True)

    class Meta:
        model = ReportReview
        fields = [
            "id",
            "report_id",
            "report",
            "verification_status",
            "verification_status_display",
            "rejection_reason",
            "handling_status",
            "handling_status_display",
            "follow_up",
            "follow_up_display",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
            "is_pending",
            "is_accepted",
            "is_rejected",
            "next_handling",
            "next_handling_label",
            "can_set_follow_up",
            "pickup_claims",
        ]
        read_only_fields = fields


class RejectReportSerializer(serializers.Serializer):
    reason = serializers.CharField(
        max_length=ReportReview.MAX_REASON_LENGTH,
        trim_whitespace=True
    )


class HandlingUpdateSerializer(serializers.Serializer):
    handling_status = serializers.ChoiceField(
        choices=[
            (value, label)
            for value, label in ReportReview.Handling.choices
            if value != ReportReview.Handling.NOT_STARTED
        ]
    )


class FollowUpUpdateSerializer(serializers.Serializer):
    follow_up = serializers.ChoiceField(
        choices=[
            (value, label)
            for value, label in ReportReview.FollowUp.choices
            if value
        ]
    )
