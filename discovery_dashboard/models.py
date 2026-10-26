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
            hasil = hasil.filter(event__icontains=acara)

        return hasil


class DiscoveryReport(Report):
    objects = DiscoveryQuerySet.as_manager()

    class Meta:
        proxy = True
        verbose_name = "Discovery Report"
