# Generated by Django 3.2.18 on 2023-03-24 11:37

from django.db import migrations


def migrate_associate_existing_topics(apps, app_schema):
    """Pre-populate the existing course pages with the topics from their associated courses"""

    CoursePage = apps.get_model("cms", "CoursePage")
    ExternalCoursePage = apps.get_model("cms", "ExternalCoursePage")
    CourseTopic = apps.get_model("courses", "CourseTopic")

    for internal_course_page in CoursePage.objects.all():
        if internal_course_page.course:
            topics = CourseTopic.objects.filter(course=internal_course_page.course)
            for topic in topics:
                CoursePage.topics.through.objects.create(
                    coursepage_id=internal_course_page.id, coursetopic_id=topic.id
                )

    for external_course_page in ExternalCoursePage.objects.all():
        if external_course_page.course:
            topics = CourseTopic.objects.filter(course=external_course_page.course)
            for topic in topics:
                ExternalCoursePage.topics.through.objects.create(
                    externalcoursepage_id=external_course_page.id,
                    coursetopic_id=topic.id,
                )


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0055_associate_courseware_page_with_topics"),
    ]

    operations = [
        migrations.RunPython(
            migrate_associate_existing_topics, migrations.RunPython.noop
        )
    ]
