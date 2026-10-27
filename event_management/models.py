from django.db import models
from django.conf import settings

class Event(models.Model):
    name = models.CharField(max_length=200)
    event_date = models.DateTimeField() 
    #data field krn simpen  tanggal and jam
    description = models.TextField()

    #lokasi event
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
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

    def __str__(self):
        return self.name