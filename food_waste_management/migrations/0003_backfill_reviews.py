from django.db import migrations


def create_missing_reviews(apps, schema_editor):
    """Laporan yang sudah ada sebelum modul ini dibuat ikut masuk antrean."""
    Report = apps.get_model('food_waste_reporting', 'Report')
    ReportReview = apps.get_model('food_waste_management', 'ReportReview')
    existing = set(ReportReview.objects.values_list('report_id', flat=True))
    ReportReview.objects.bulk_create(
        [ReportReview(report_id=pk) for pk in Report.objects.values_list('pk', flat=True) if pk not in existing]
    )


class Migration(migrations.Migration):

    dependencies = [
        ('food_waste_management', '0002_reportreview'),
    ]

    operations = [
        migrations.RunPython(create_missing_reviews, migrations.RunPython.noop),
    ]