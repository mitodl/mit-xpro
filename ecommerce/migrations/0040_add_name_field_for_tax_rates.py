# Generated by Django 3.2.21 on 2023-09-22 16:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ecommerce", "0039_add_taxrate_table"),
    ]

    operations = [
        migrations.AddField(
            model_name="taxrate",
            name="tax_rate_name",
            field=models.CharField(default="VAT", max_length=100, null=True),
        ),
    ]