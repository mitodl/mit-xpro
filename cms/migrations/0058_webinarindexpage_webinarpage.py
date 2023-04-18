# Generated by Django 3.2.18 on 2023-04-18 12:59

from django.db import migrations, models
import django.db.models.deletion
import wagtailmetadata.models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailimages", "0023_add_choose_permissions"),
        ("wagtailcore", "0062_comment_models_and_pagesubscription"),
        ("cms", "0057_mark_topics_not_required"),
    ]

    operations = [
        migrations.CreateModel(
            name="WebinarIndexPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
        migrations.CreateModel(
            name="WebinarPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[("UPCOMING", "UPCOMING"), ("ON-DEMAND", "ON-DEMAND")],
                        max_length=20,
                    ),
                ),
                (
                    "start_datetime",
                    models.DateTimeField(
                        blank=True,
                        help_text="The start date and time of the webinar.",
                        null=True,
                    ),
                ),
                (
                    "duration",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="The duration of the webinar in Minutes.",
                        null=True,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True, help_text="Description for the webinar.", null=True
                    ),
                ),
                (
                    "action_title",
                    models.CharField(
                        help_text="The text to show on the call to action button i.e. REGISTER, VIEW RECORDING",
                        max_length=255,
                    ),
                ),
                (
                    "action_url",
                    models.URLField(
                        help_text="The URL to go to when the action button is clicked."
                    ),
                ),
                (
                    "banner_image",
                    models.ForeignKey(
                        help_text="Image for the Webinar.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="wagtailimages.image",
                    ),
                ),
                (
                    "search_image",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="wagtailimages.image",
                        verbose_name="Search image",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(
                wagtailmetadata.models.MetadataMixin,
                "wagtailcore.page",
                models.Model,
            ),
        ),
    ]