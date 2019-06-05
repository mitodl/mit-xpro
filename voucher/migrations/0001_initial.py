# Generated by Django 2.1.7 on 2019-05-31 18:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("ecommerce", "0011_rename_bulk_enrollment_delivery"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Voucher",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("voucher_id", models.CharField(blank=True, max_length=32, null=True)),
                ("employee_id", models.CharField(max_length=32)),
                ("employee_name", models.CharField(max_length=128)),
                ("course_start_date_input", models.DateField()),
                ("course_id_input", models.CharField(max_length=255)),
                ("course_title_input", models.CharField(max_length=255)),
                ("pdf", models.FileField(null=True, upload_to="vouchers/")),
                ("uploaded", models.DateTimeField(auto_now_add=True)),
                (
                    "coupon",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="voucher",
                        to="ecommerce.Coupon",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vouchers",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False},
        )
    ]
