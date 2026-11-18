from django.utils import timezone
from rest_framework import serializers

from food_waste_reporting.models import Report


class ReportSerializer(serializers.ModelSerializer):
    reported_by_username = serializers.CharField(
        source="reported_by.username", read_only=True
    )
    event_label = serializers.CharField(read_only=True)
    food_portion = serializers.IntegerField(min_value=1)
    event = serializers.CharField(max_length=255, required=False, allow_blank=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "reported_by",
            "reported_by_username",
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
        read_only_fields = ["id", "reported_by", "created_at"]

    def validate_best_before(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Waktu kedaluwarsa harus di waktu yang akan datang.")
        return value

    def validate(self, attrs):
        related_event = attrs.get(
            "related_event", getattr(self.instance, "related_event", None)
        )
        event = attrs.get("event", getattr(self.instance, "event", ""))

        if not related_event and not (event or "").strip():
            raise serializers.ValidationError(
                {"event": "Isi dengan event yang valid."}
            )

        if related_event and not (event or "").strip():
            attrs["event"] = related_event.name

        return attrs