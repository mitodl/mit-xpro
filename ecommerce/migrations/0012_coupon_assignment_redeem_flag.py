# Generated by Django 2.1.7 on 2019-05-29 20:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("ecommerce", "0011_rename_bulk_enrollment_delivery")]

    operations = [
        migrations.AddField(
            model_name="productcouponassignment",
            name="redeemed",
            field=models.BooleanField(default=False),
        )
    ]
