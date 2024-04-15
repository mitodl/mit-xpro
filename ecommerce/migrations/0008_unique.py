# Generated by Django 2.1.7 on 2019-04-30 17:41

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0006_update_related_name"),
        ("ecommerce", "0007_add_bulk_enrollment_delivery"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="couponeligibility", unique_together={("coupon", "product")}
        ),
        migrations.AlterUniqueTogether(
            name="couponredemption", unique_together={("coupon_version", "order")}
        ),
        migrations.AlterUniqueTogether(
            name="couponselection", unique_together={("coupon", "basket")}
        ),
        migrations.AlterUniqueTogether(
            name="courserunenrollment", unique_together={("order", "run")}
        ),
        migrations.AlterUniqueTogether(
            name="courserunselection", unique_together={("basket", "run")}
        ),
    ]
