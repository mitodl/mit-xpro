# Generated by Django 3.2.23 on 2024-02-07 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("b2b_ecommerce", "0010_b2bline"),
    ]

    operations = [
        migrations.AlterField(
            model_name="b2bcoupon",
            name="coupon_code",
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
