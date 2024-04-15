# Generated by Django 2.2.20 on 2021-05-05 08:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ecommerce", "0031_productcouponassignment_original_email")]

    operations = [
        migrations.AddField(
            model_name="dataconsentagreement",
            name="is_global",
            field=models.BooleanField(
                default=False,
                help_text="When selected it will override the value of the courses field below",
                verbose_name="All Courses",
            ),
        ),
        migrations.AlterField(
            model_name="dataconsentagreement",
            name="courses",
            field=models.ManyToManyField(blank=True, to="courses.Course"),
        ),
    ]
