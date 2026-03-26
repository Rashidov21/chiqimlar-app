from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_donation_status_and_reason"),
    ]

    operations = [
        migrations.AddField(
            model_name="donation",
            name="telegram_username_snapshot",
            field=models.CharField(
                blank=True,
                help_text="Screenshot yuborilgan paytdagi Telegram username.",
                max_length=64,
            ),
        ),
        migrations.AddField(
            model_name="donation",
            name="screenshot_file_id",
            field=models.CharField(
                blank=True,
                help_text="Telegram photo file_id (admin preview uchun).",
                max_length=255,
            ),
        ),
    ]
