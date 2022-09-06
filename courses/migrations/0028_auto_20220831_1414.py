# Generated by Django 3.2.14 on 2022-08-31 14:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0062_comment_models_and_pagesubscription"),
        ("courses", "0027_jsonField_from_django_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="courseruncertificate",
            name="certificate_page_revision",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="wagtailcore.pagerevision",
            ),
        ),
        migrations.AddField(
            model_name="programcertificate",
            name="certificate_page_revision",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="wagtailcore.pagerevision",
            ),
        ),
    ]
