from django.conf import settings
from django.db import migrations


def create_missing_profiles(apps, schema_editor):
    """Akun yang sudah ada sebelum modul profil dibuat ikut mendapat profil kosong."""
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    Profile = apps.get_model('authentication', 'Profile')
    existing = set(Profile.objects.values_list('user_id', flat=True))
    Profile.objects.bulk_create(
        [Profile(user_id=pk) for pk in User.objects.values_list('pk', flat=True) if pk not in existing]
    )


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(create_missing_profiles, migrations.RunPython.noop),
    ]
