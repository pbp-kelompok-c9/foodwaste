from django.db.models.fields import *
from django.forms.fields import *
from django.forms.models import ModelChoiceField, ModelForm
from django.forms.widgets import *
from food_waste_reporting.models import Report
from event_management.models import Event

class ReportForm(ModelForm):
    food_name = CharField(
        label="Jenis Makanan",
        widget=TextInput(
            attrs={
                "placeholder": "Ayam Goreng",
                "maxlength": 255,
            }
        )
    )

    food_portion = IntegerField(
        label="Porsi",
        min_value=0,
        widget=NumberInput(
            attrs={
                "placeholder": "5"
            }
        ),
    )

    best_before = DateTimeField(
        label="Waktu Kedaluwarsa",
        input_formats=["%d/%m/%Y"],  
        widget=DateTimeInput(
            format="%d/%m/%Y",
            attrs={
                "placeholder": "6/10/2026",
            }
        )
    )

    location = CharField(
        label="Lokasi",
        widget=TextInput(
            attrs={
                "placeholder": "Dekat Pintu A, PBP Convention Hall",
                "maxlength": 255,
            }
        )
    )

    related_event = ModelChoiceField(
        label="Event",
        queryset=Event.objects.order_by("event_date", "name", "pk"),
        empty_label="Pilih event",
        widget=Select(attrs={"class": "input"}),
        help_text="Pilih acara yang sudah dibuat EO. Jika belum ada, minta EO membuat acara dahulu.",
    )

    pickup_option = ChoiceField(
        label="Opsi Penjemputan",
        choices = Report.PICKUP_OPTIONS,
        widget=Select(attrs={'class': 'input'})
    )

    details = CharField(
        label="Deskripsi Tambahan",
        widget=Textarea(
            attrs={
                "placeholder": "Bisa kontak @pbpc9 di LINE untuk info lebih lanjut",
                "rows": 3,
            }
        )
    )


    class Meta:
        model = Report
        fields = [
            "food_name",
            "food_portion",
            "best_before",
            "location",
            "related_event",
            "pickup_option",
            "details",
        ]

    def save(self, commit=True):
        report = super().save(commit=False)
        # Store a text snapshot too, so old consumers/data exports retain a name.
        report.event = report.related_event.name
        if commit:
            report.save()
            self.save_m2m()
        return report
