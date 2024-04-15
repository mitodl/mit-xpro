# Generated by Django 2.1.7 on 2019-06-12 03:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("cms", "0031_setup_catalog_page")]

    operations = [
        migrations.AlterField(
            model_name="coursepage",
            name="video_url",
            field=models.URLField(
                blank=True,
                help_text="URL to the video to be displayed for this program/course. Must be an HLS video URL.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="programpage",
            name="video_url",
            field=models.URLField(
                blank=True,
                help_text="URL to the video to be displayed for this program/course. Must be an HLS video URL.",
                null=True,
            ),
        ),
    ]
