# Generated by Django 2.2.10 on 2020-02-27 12:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ecommerce", "0025_add_programrun_models")]

    operations = [
        migrations.AddField(
            model_name="coupon",
            name="include_future_runs",
            field=models.BooleanField(default=True),
        )
    ]
