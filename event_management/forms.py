from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    event_date = forms.DateTimeField(
        label="Tanggal dan waktu acara (WIB)",
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
            "latitude": "Latitude",
            "longitude": "Longitude",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Nama acara", "maxlength": 200}),
            "description": forms.Textarea(attrs={"rows": 5}),
            "location": forms.TextInput(attrs={"placeholder": "Alamat atau nama tempat"}),
            "latitude": forms.NumberInput(attrs={"step": "0.000001", "min": -90, "max": 90}),
            "longitude": forms.NumberInput(attrs={"step": "0.000001", "min": -180, "max": 180}),
        }
        help_texts = {
            "event_date": "Waktu Indonesia Barat (UTC+7).",
            "location": "Pilih hasil pencarian lokasi atau isi alamat secara manual.",
            "latitude": "Opsional. Isi kedua koordinat, atau kosongkan keduanya.",
        }
