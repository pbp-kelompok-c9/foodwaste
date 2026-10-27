from django.db import migrations


def create_eo_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.using(schema_editor.connection.alias).get_or_create(name="EO")


class Migration(migrations.Migration):
    dependencies = [
        ("event_management", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        # Keep memberships if this migration is rolled back and reapplied.
        migrations.RunPython(create_eo_group, reverse_code=migrations.RunPython.noop),
    ]
