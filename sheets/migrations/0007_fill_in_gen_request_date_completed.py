# Generated by Django 2.2.4 on 2019-12-06 18:04
import datetime

from django.db import migrations


def now_in_utc():
    """
    Get the current time in UTC

    Returns:
        datetime.datetime: A datetime object for the current time
    """
    return datetime.datetime.now(tz=datetime.timezone.utc)


def set_date_completed_to_none(apps, schema_editor):
    """
    Set all date_completed field values to None
    """
    CouponGenerationRequest = apps.get_model("sheets", "CouponGenerationRequest")
    CouponGenerationRequest.objects.exclude(date_completed=None).update(
        date_completed=None
    )


def fill_in_date_completed(apps, schema_editor):
    """
    Set all date_completed field value to the current datetime
    """
    now = now_in_utc()
    CouponGenerationRequest = apps.get_model("sheets", "CouponGenerationRequest")
    CouponGenerationRequest.objects.filter(completed=True, date_completed=None).update(
        date_completed=now
    )


class Migration(migrations.Migration):
    dependencies = [("sheets", "0006_coupon_gen_request_err_handling_fields")]

    operations = [
        migrations.RunPython(fill_in_date_completed, set_date_completed_to_none)
    ]
