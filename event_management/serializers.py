from copy import copy

from rest_framework import serializers

from .forms import EventForm
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )

    class Meta:
        model = Event
        fields = [
            "id", "name", "event_date", "description", "location",
            "latitude", "longitude", "created_by", "created_by_username",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        # Merge PATCH data with the saved values before applying web validation.
        data = {
            field: attrs.get(field, getattr(self.instance, field, None))
            for field in EventForm.Meta.fields
        }
        if self.instance and data["event_date"] == self.instance.event_date:
            data["event_date"] = self.instance.event_date.replace(
                second=0, microsecond=0
            )
        form = EventForm(data=data, instance=copy(self.instance))
        if not form.is_valid():
            raise serializers.ValidationError({
                "non_field_errors" if field == "__all__" else field: messages
                for field, messages in form.errors.items()
            })
        return {field: form.cleaned_data[field] for field in EventForm.Meta.fields}
