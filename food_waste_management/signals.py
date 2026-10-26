from django.db.models.signals import post_save
from django.dispatch import receiver

from food_waste_reporting.models import Report
from food_waste_management.models import ReportReview


@receiver(post_save, sender=Report)
def create_review_for_new_report(sender, instance, created, **kwargs):
    """Setiap laporan baru otomatis masuk antrean verifikasi."""
    if created:
        ReportReview.objects.get_or_create(report=instance)