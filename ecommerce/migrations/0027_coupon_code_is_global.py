# Generated by Django 2.2.8 on 2020-02-12 12:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ecommerce", "0026_coupon_include_future_runs")]

    operations = [
        migrations.AddField(
            model_name="coupon",
            name="is_global",
            field=models.BooleanField(default=False),
        )
    ]
