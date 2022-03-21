# Generated by Django 3.2.11 on 2022-02-22 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("courses", "0026_nullify_expiration_date")]

    operations = [
        migrations.AlterField(
            model_name="courserunenrollmentaudit",
            name="data_after",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="courserunenrollmentaudit",
            name="data_before",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="courserungradeaudit",
            name="data_after",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="courserungradeaudit",
            name="data_before",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="programenrollmentaudit",
            name="data_after",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="programenrollmentaudit",
            name="data_before",
            field=models.JSONField(blank=True, null=True),
        ),
    ]