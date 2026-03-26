from django.db import migrations, models


def seed_status_from_confirmed(apps, schema_editor):
    Donation = apps.get_model("accounts", "Donation")
    Donation.objects.filter(confirmed=True).update(status="approved")
    Donation.objects.filter(confirmed=False).update(status="pending")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_add_supporter_and_required_channels"),
    ]

    operations = [
        migrations.AddField(
            model_name="donation",
            name="status",
            field=models.CharField(
                choices=[("pending", "Tekshiruvda"), ("approved", "Tasdiqlangan"), ("rejected", "Rad etilgan")],
                db_index=True,
                default="pending",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="donation",
            name="rejection_reason",
            field=models.CharField(blank=True, help_text="Rad etish sababi (ixtiyoriy).", max_length=255),
        ),
        migrations.RunPython(seed_status_from_confirmed, migrations.RunPython.noop),
    ]
