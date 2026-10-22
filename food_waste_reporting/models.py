import uuid

from django.db import models
from django.contrib.auth.models import User

class Report(models.Model):
    PICKUP_OPTIONS = [
        ("ambil sendiri", "Ambil Sendiri"),
        ("diantar", "Diantar")
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    food_name = models.CharField(max_length=255)
    food_portion = models.PositiveIntegerField()
    best_before = models.DateTimeField()
    location = models.CharField(max_length=255)
    event = models.CharField(max_length=255)
    pickup_option = models.CharField(max_length=255, choices=PICKUP_OPTIONS)
    details = models.TextField()
    picture = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]