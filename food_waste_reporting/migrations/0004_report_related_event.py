"""Add the event link without rewriting or discarding legacy event text."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("event_management", "0001_initial"),
        ("food_waste_reporting", "0003_alter_report_pickup_option"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="related_event",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="reports",
                to="event_management.event",
            ),
        ),
    ]
