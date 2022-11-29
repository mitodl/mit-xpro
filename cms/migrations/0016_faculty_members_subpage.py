# Generated by Django 2.1.7 on 2019-05-06 15:25

from django.db import migrations, models
import django.db.models.deletion
import wagtail.blocks
import wagtail.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0041_group_collection_permissions_verbose_name_plural"),
        ("cms", "0015_user_testimonials_subpage"),
    ]

    operations = [
        migrations.CreateModel(
            name="FacultyMembersPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.Page",
                    ),
                ),
                (
                    "heading",
                    models.CharField(
                        help_text="The heading to display for this section on the product page.",
                        max_length=255,
                    ),
                ),
                (
                    "subhead",
                    models.CharField(
                        help_text="The subhead to display for this section on the product page.",
                        max_length=255,
                    ),
                ),
                (
                    "members",
                    wagtail.fields.StreamField(
                        [
                            (
                                "member",
                                wagtail.blocks.StructBlock(
                                    [
                                        (
                                            "name",
                                            wagtail.blocks.CharBlock(
                                                help_text="Name of the faculty member.",
                                                max_length=100,
                                            ),
                                        ),
                                        (
                                            "image",
                                            wagtail.images.blocks.ImageChooserBlock(
                                                help_text="Profile image size must be at least 300x300 pixels."
                                            ),
                                        ),
                                        (
                                            "description",
                                            wagtail.blocks.RichTextBlock(
                                                help_text="A brief description about the faculty member."
                                            ),
                                        ),
                                    ]
                                ),
                            )
                        ],
                        help_text="The faculty members to display on this page",
                    ),
                ),
            ],
            options={"abstract": False},
            bases=("wagtailcore.page",),
        )
    ]
