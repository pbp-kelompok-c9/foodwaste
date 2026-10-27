
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
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


class PickupClaim(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Menunggu Foto"
        REVIEW = "REVIEW", "Menunggu Verifikasi Admin"
        SUCCESS = "SUCCESS", "Disetujui Admin"
        REJECTED = "REJECTED", "Ditolak Admin"
        EXPIRED = "EXPIRED", "Waktu Habis"

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
        max_length=20,
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

    uploaded_at = models.DateTimeField(
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
                condition=Q(
                    status__in=["PENDING", "REVIEW", "SUCCESS"]
                ),
                name="one_active_pickup_per_report"
            )
        ]

    def is_expired(self):
        return (
            self.status == self.Status.PENDING
            and timezone.now() >= self.expired_at
        )

    def __str__(self):
        return (
            f"{self.report.food_name} - "
            f"{self.user} - "
            f"{self.get_status_display()}"
        )
