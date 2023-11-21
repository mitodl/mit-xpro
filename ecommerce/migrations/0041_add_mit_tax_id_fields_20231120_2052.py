# Generated by Django 3.2.23 on 2023-11-20 20:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ecommerce", "0040_alter_taxrate_tax_rate"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="mit_tax_identifier",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="ecommerce.taxrate",
            ),
        ),
        migrations.AddField(
            model_name="taxrate",
            name="tax_identifier",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="taxrate",
            name="tax_identifier_name",
            field=models.CharField(default="GSTIN", max_length=100, null=True),
        ),
    ]
