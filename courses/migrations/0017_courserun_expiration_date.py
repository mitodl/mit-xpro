# Generated by Django 2.2.3 on 2019-08-06 07:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("courses", "0016_enrollment_order")]

    operations = [
        migrations.AddField(
            model_name="courserun",
            name="expiration_date",
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                help_text="When empty, set to 90 days past end date.",
                null=True,
            ),
        )
    ]
