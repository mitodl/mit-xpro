# Generated by Django 2.1.7 on 2019-05-09 11:46

from django.db import migrations, models
import django.db.models.deletion
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0041_group_collection_permissions_verbose_name_plural"),
        ("cms", "0013_courses_in_program_subpage"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResourcePage",
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
                    "sub_heading",
                    models.CharField(
                        help_text="Sub heading of the resource page.",
                        max_length=250,
                        null=True,
                    ),
                ),
                (
                    "content",
                    wagtail.fields.StreamField(
                        [
                            (
                                "content",
                                wagtail.blocks.StructBlock(
                                    [
                                        (
                                            "heading",
                                            wagtail.blocks.CharBlock(max_length=100),
                                        ),
                                        ("detail", wagtail.blocks.RichTextBlock()),
                                    ]
                                ),
                            )
                        ],
                        help_text="Enter details of content.",
                    ),
                ),
            ],
            options={"abstract": False},
            bases=("wagtailcore.page",),
        )
    ]
