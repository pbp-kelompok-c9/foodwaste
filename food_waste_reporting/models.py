import uuid

from django.db import models

class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    food_name = models.CharField(max_length=255)
    food_portion = models.PositiveIntegerField()
    best_before = models.DateTimeField()
    location = models.CharField(max_length=255)
    event = models.CharField(max_length=255)
    pickup_option = models.CharField(max_length=255)
    details = models.TextField()
    picture = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)