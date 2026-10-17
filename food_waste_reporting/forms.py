from django.db.models.fields import *
from django.forms.fields import *
from django.forms.models import ModelForm
from django.forms.widgets import *
from food_waste_reporting.models import Report

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

    best_before = DateField(
        label="Waktu Kedaluwarsa",
        widget=DateInput(
            attrs={
                "placeholder": "6/10/2026"
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

    event = CharField(
        label="Event",
        widget=TextInput(
            attrs={
                "placeholder": "Burhan & Sofita Wedding",
                "maxlength": 255,
            }
        )
    )

    pickup_options = ChoiceField(
        label="Opsi Penjemputan",
        choices = ["Ambil Sendiri", "ambil sendiri", "Diantar", "diantar"],
        widget=Select(attrs={'class': 'dropdown'})
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
            "event",
            "pickup_options",
            "details",
        ]