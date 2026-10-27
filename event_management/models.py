from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Event(models.Model):
    name = models.CharField(max_length=200)
    event_date = models.DateTimeField()
    description = models.TextField()

    location = models.CharField(max_length=255)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )

    # Relasi event dengan akun EO
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='organized_events'
    )

    # Waktu pembuatan dan perubahan data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-event_date", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(latitude__isnull=True)
                | models.Q(latitude__gte=-90, latitude__lte=90),
                name="event_latitude_range",
            ),
            models.CheckConstraint(
                condition=models.Q(longitude__isnull=True)
                | models.Q(longitude__gte=-180, longitude__lte=180),
                name="event_longitude_range",
            ),
            models.CheckConstraint(
                condition=models.Q(latitude__isnull=True, longitude__isnull=True)
                | models.Q(latitude__isnull=False, longitude__isnull=False),
                name="event_coordinates_pair",
            ),
        ]

    def clean(self):
        super().clean()
        if (self.latitude is None) != (self.longitude is None):
            raise ValidationError("Lokasi peta belum lengkap. Pilih lokasi lagi atau ketik ulang alamat.")

    def __str__(self):
        return self.name


class LocationSearchState(models.Model):
    """Shared provider cache and request gate, including across web workers."""

    key = models.CharField(max_length=64, primary_key=True)
    payload = models.JSONField(default=list, blank=True)
    expires_at = models.DateTimeField(db_index=True)
