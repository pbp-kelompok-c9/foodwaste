from django.db import models
from django.db.models import Q
from food_waste_reporting.models import Report


class DiscoveryQuerySet(models.QuerySet):

    def cari(self, keyword="", lokasi="", acara=""):
        hasil = self

        if keyword:
            hasil = hasil.filter(
                Q(food_name__icontains=keyword) |
                Q(details__icontains=keyword)
            )

        if lokasi:
            hasil = hasil.filter(location__icontains=lokasi)

        if acara:
            hasil = hasil.filter(
                Q(related_event__name__icontains=acara)
                | Q(related_event__isnull=True, event__icontains=acara)
            )

        return hasil.select_related("related_event")


class DiscoveryReport(Report):
    objects = DiscoveryQuerySet.as_manager()

    class Meta:
        proxy = True
        verbose_name = "Discovery Report"
