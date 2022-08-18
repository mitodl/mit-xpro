# Generated by Django 3.2.14 on 2022-08-18 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cms", "0053_certificatepage_partner_logo")]

    operations = [
        migrations.AddField(
            model_name="certificatepage",
            name="institute_text",
            field=models.CharField(
                blank=True,
                help_text="Specify the institute text",
                max_length=250,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="certificatepage",
            name="partner_logo_placement",
            field=models.IntegerField(
                blank=True,
                choices=[(None, "Do not display"), (1, "First"), (2, "Second")],
                default=2,
                help_text="Partner logo placement on certificate",
                null=True,
            ),
        ),
    ]
