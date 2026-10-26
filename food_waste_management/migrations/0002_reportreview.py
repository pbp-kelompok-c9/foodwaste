import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('food_waste_reporting', '0003_alter_report_pickup_option'),
        ('food_waste_management', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('verification_status', models.CharField(choices=[('menunggu', 'Menunggu'), ('diterima', 'Diterima'), ('ditolak', 'Ditolak')], db_index=True, default='menunggu', max_length=20)),
                ('rejection_reason', models.TextField(blank=True, default='')),
                ('handling_status', models.CharField(choices=[('belum_diproses', 'Belum Diproses'), ('menunggu_penjemputan', 'Menunggu Penjemputan'), ('sudah_diperiksa', 'Sudah Diperiksa'), ('selesai', 'Selesai')], default='belum_diproses', max_length=30)),
                ('follow_up', models.CharField(blank=True, choices=[('', 'Belum Ditentukan'), ('dijual', 'Dijual'), ('dibagikan', 'Dibagikan'), ('diolah', 'Diolah')], default='', max_length=20)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('report', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='review', to='food_waste_reporting.report')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]