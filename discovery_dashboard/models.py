from django.db import models
from django.db.models import Q
from food_waste_reporting.models import Report
from datetime import timedelta
from django.conf import settings
from django.utils import timezone


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

class PickupClaim(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        EXPIRED = "EXPIRED", "Expired"

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="pickup_claims"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )

    created_at = models.DateTimeField(default=timezone.now)

    expired_at = models.DateTimeField()

    proof_photo = models.ImageField(
        upload_to="pickup_proofs/",
        blank=True,
        null=True
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["report"],
                condition=models.Q(
                    status__in=["PENDING", "SUCCESS"]
                ),
                name="one_active_pickup_per_report"
            )
        ]

    def is_expired(self):
        return timezone.now() >= self.expired_at