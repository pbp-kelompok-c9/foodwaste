from django import forms
from django.utils import timezone
from .models import Event


class EventForm(forms.ModelForm):
    event_date = forms.DateTimeField(
        label="Tanggal dan waktu acara (WIB)",
        help_text="Pilih waktu sekarang atau yang akan datang (WIB, UTC+7).",
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
        labels = {
            "name": "Nama acara",
            "description": "Detail acara",
            "location": "Alamat lokasi",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Nama acara", "maxlength": 200}),
            "description": forms.Textarea(attrs={"rows": 5}),
            "location": forms.TextInput(attrs={"placeholder": "Alamat atau nama tempat"}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
        }
        help_texts = {
            "location": "Pilih hasil pencarian lokasi atau isi alamat secara manual.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_event_date = (
            None if self.instance._state.adding else self.instance.event_date
        )
        minimum = timezone.localtime().replace(second=0, microsecond=0)
        # An existing past date must remain editable without rewriting history.
        if self._original_event_date is None or self._original_event_date >= minimum:
            self.fields["event_date"].widget.attrs["min"] = minimum.strftime("%Y-%m-%dT%H:%M")

    def clean_event_date(self):
        event_date = self.cleaned_data["event_date"]
        original = self._original_event_date
        if original is not None and event_date == original.replace(second=0, microsecond=0):
            return original
        # The datetime-local field accepts minutes, so compare at that precision.
        if event_date < timezone.now().replace(second=0, microsecond=0):
            raise forms.ValidationError(
                "Tanggal dan waktu acara tidak boleh sudah lewat.", code="past_event_date"
            )
        return event_date
