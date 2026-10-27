from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    event_date = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M"
        )
    )

    class Meta:
        model = Event
        fields = [
            "name",
            "event_date",
            "description",
            "location",
            "latitude",
            "longitude",
        ]
