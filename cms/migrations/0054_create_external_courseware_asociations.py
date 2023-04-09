# Generated by Django 3.2.18 on 2023-03-16 12:26

import pytz
from datetime import datetime
from django.db import migrations, models
import django.db.models.deletion

# Importing here because we need to use methods from this model and replicating the functionality
# would make the migrations complex since it would include replication of some of the Wagtail's Page model.
from cms.models import ExternalProgramPage


def get_zone_aware_datetime(date):
    """Takes a date object and returns a zone aware datetime"""
    return datetime.combine(date, datetime.max.time(), pytz.UTC) if date else None


def check_and_generate_associated_product(
    apps, schema_editor, external_courseware, courseware_run_id
):
    """Check and create an associated product if needed"""
    ContentType = apps.get_model("contenttypes", "ContentType")
    ExternalCoursePage = apps.get_model("cms", "ExternalCoursePage")
    Product = apps.get_model("ecommerce", "Product")
    ProductVersion = apps.get_model("ecommerce", "ProductVersion")

    if external_courseware.price:
        if isinstance(external_courseware, ExternalCoursePage):
            courseware_content_type = ContentType.objects.get(
                app_label="courses", model="courserun"
            )
        else:
            courseware_content_type = ContentType.objects.get(
                app_label="courses", model="program"
            )

        generated_product = Product.objects.create(
            content_type=courseware_content_type,
            object_id=courseware_run_id,
            is_active=True,
        )
        ProductVersion.objects.create(
            product=generated_product,
            price=external_courseware.price,
            text_id=external_courseware.readable_id,
            description=external_courseware.title,
        )


def migrate_external_courses(apps, schema_editor):
    """Associate external course pages to Django course models"""
    Course = apps.get_model("courses", "Course")
    CourseRun = apps.get_model("courses", "CourseRun")
    ExternalCoursePage = apps.get_model("cms", "ExternalCoursePage")

    external_courses = ExternalCoursePage.objects.all()
    for external_course in external_courses:
        # It is possible that we might find a course with same readable Id, In this case let's just mark that
        # as external and not change other things to keep on safe side from overwriting data.
        generated_course, is_created = Course.objects.get_or_create(
            readable_id=external_course.readable_id,
            defaults={
                "is_external": True,
                "title": external_course.title,
                "live" "": external_course.live,
            },
        )
        # If already exists, Just set value for newly added field
        if not is_created:
            generated_course.is_external = True
            generated_course.save()

        # It's possible for a course to have multiple runs already created in the system, To be on safe side if we get
        # existing course runs let's just update the external URL in them to be on safe side
        generated_course_run = None
        existing_course_runs = CourseRun.objects.filter(course=generated_course)
        if existing_course_runs.exists():
            existing_course_runs.update(
                external_marketing_url=external_course.external_url
            )
        else:
            generated_course_run, _ = CourseRun.objects.get_or_create(
                course=generated_course,
                title=generated_course.title,
                start_date=get_zone_aware_datetime(external_course.start_date),
                courseware_id=external_course.readable_id,
                external_marketing_url=external_course.external_url,
                live=generated_course.live,
                run_tag="R1",
            )
        # To be safe, Let's create products only if there was no existing course run and we created the first one ever
        if generated_course_run:
            check_and_generate_associated_product(
                apps, schema_editor, external_course, generated_course_run.id
            )
        external_course.course = generated_course
        external_course.save()


def migrate_external_programs(apps, schema_editor):
    """Associate external program pages to Django program models"""
    # Migrate external programs
    Program = apps.get_model("courses", "Program")
    ProgramRun = apps.get_model("courses", "ProgramRun")

    external_programs = ExternalProgramPage.objects.all()
    for external_program in external_programs:
        # It is possible that we might find a program with same readable Id, In this case let's just mark that
        # as external and not change other things to be on safe side from overwriting data.

        generated_program, is_created = Program.objects.get_or_create(
            readable_id=external_program.readable_id,
            defaults={
                "is_external": True,
                "title": external_program.title,
                "live": external_program.live,
            },
        )
        # If already exists, Just set value for newly added field
        if not is_created:
            generated_program.is_external = True
            generated_program.save()

        program_course_lineup = (
            external_program.course_lineup.content_pages
            if external_program.course_lineup
            else []
        )
        for idx, course_in_program in enumerate(program_course_lineup):
            course_in_program.course.program_id = generated_program.id
            course_in_program.course.position_in_program = idx + 1
            course_in_program.course.save()

        # It's possible that we might have existing runs for this program
        existing_programs = ProgramRun.objects.filter(program=generated_program)
        if existing_programs.exists():
            existing_programs.objects.update(
                external_marketing_url=external_program.external_url
            )
        else:
            generated_program_run, _ = ProgramRun.objects.get_or_create(
                program=generated_program,
                external_marketing_url=external_program.external_url,
                start_date=get_zone_aware_datetime(external_program.start_date),
                run_tag="R1",
            )
        # To be safe, Let's create product only if there was no existing program we created the first one ever
        if is_created:
            check_and_generate_associated_product(
                apps, schema_editor, external_program, generated_program.id
            )

        external_program.program_id = generated_program.id
        external_program.save()


def migrate_external_courseware(apps, schema_editor):
    """Migrate the existing external courseware pages to Courseware(Course, Program) Django models"""

    migrate_external_courses(apps, schema_editor)
    migrate_external_programs(apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0030_add_courseware_external_fields"),
        ("cms", "0053_certificatepage_partner_logo"),
    ]

    operations = [
        migrations.AddField(
            model_name="externalcoursepage",
            name="course",
            field=models.OneToOneField(
                help_text="The course for this page",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="courses.course",
            ),
        ),
        migrations.AddField(
            model_name="externalprogrampage",
            name="program",
            field=models.OneToOneField(
                help_text="The program for this page",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="courses.program",
            ),
        ),
        migrations.AlterField(
            model_name="externalcoursepage",
            name="external_url",
            field=models.URLField(
                blank=True,
                help_text="The URL of the external course web page.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="externalcoursepage",
            name="readable_id",
            field=models.CharField(
                blank=True,
                help_text="The readable ID of the external course. Appears in URL, has to be unique.",
                max_length=64,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="externalprogrampage",
            name="course_count",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="The number of total courses in the external program.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="externalprogrampage",
            name="external_url",
            field=models.URLField(
                blank=True,
                help_text="The URL of the external program web page.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="externalprogrampage",
            name="readable_id",
            field=models.CharField(
                blank=True,
                help_text="The readable ID of the external program. Appears in URL, has to be unique.",
                max_length=64,
                null=True,
            ),
        ),
        migrations.RunPython(migrate_external_courseware, migrations.RunPython.noop),
    ]
