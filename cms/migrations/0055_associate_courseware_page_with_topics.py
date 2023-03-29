# Generated by Django 3.2.18 on 2023-03-24 11:36

from django.db import migrations
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0031_create_topics_sublevel"),
        ("cms", "0054_create_external_courseware_asociations"),
    ]

    operations = [
        migrations.AddField(
            model_name="coursepage",
            name="topics",
            field=modelcluster.fields.ParentalManyToManyField(
                help_text="The topics for this course page.", to="courses.CourseTopic"
            ),
        ),
        migrations.AddField(
            model_name="externalcoursepage",
            name="topics",
            field=modelcluster.fields.ParentalManyToManyField(
                help_text="The topics for this course page.", to="courses.CourseTopic"
            ),
        ),
    ]
