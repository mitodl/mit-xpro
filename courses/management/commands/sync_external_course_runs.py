"""Management command to sync external course runs"""

from django.core.management.base import BaseCommand

from courses.sync_external_courses.emeritus_api import (
    EmeritusKeyMap,
    fetch_emeritus_courses,
    update_emeritus_course_runs,
)
from mitxpro import settings


class Command(BaseCommand):
    """Sync external course runs"""

    help = "Management command to sync external course runs from the vendor APIs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--vendor-name",
            type=str,
            help="The name of the vendor i.e. `Emeritus`",
            required=True,
        )
        super().add_arguments(parser)

    def handle(self, *args, **options):  # noqa: ARG002
        """Handle command execution"""
        if not settings.FEATURES.get("ENABLE_EXTERNAL_COURSE_SYNC", False):
            self.stdout.write(
                self.style.ERROR(
                    "External Course Sync is disabled. You can enable it by turning on the feature flag "
                    "`ENABLE_EXTERNAL_COURSE_SYNC`"
                )
            )
            return

        vendor_name = options["vendor_name"]
        if vendor_name.lower() == EmeritusKeyMap.PLATFORM_NAME.value.lower():
            self.stdout.write(f"Starting course sync for {vendor_name}.")
            emeritus_course_runs = fetch_emeritus_courses()
            stats = update_emeritus_course_runs(emeritus_course_runs)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Number of Courses Created {len(stats['courses_created'])}."
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"External Course Codes: {stats['courses_created']}.\n"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Number of existing Courses {len(stats['existing_courses'])}."
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"External Course Codes: {stats['existing_courses']}.\n"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Number of Course Runs Created {len(stats['course_runs_created'])}."
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"External Course Run Codes: {stats['course_runs_created']}.\n"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Number of Course Runs Updated {len(stats['course_runs_updated'])}."
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"External Course Run Codes: {stats['course_runs_updated']}.\n"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Number of Courses Pages Created {len(stats['course_pages_created'])}."
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"External Course Codes: {stats['course_pages_created']}.\n"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Number of Courses Pages Updated {len(stats['course_pages_updated'])}."
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"External Course Codes: {stats['course_pages_updated']}.\n"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Number of Course Runs Skipped due to bad data {len(stats['course_runs_skipped'])}."
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"External Course Codes: {stats['course_runs_skipped']}.\n"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Number of Expired Course Runs {len(stats['course_runs_expired'])}."
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"External Course Codes: {stats['course_runs_expired']}.\n"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"External course sync successful for {vendor_name}."
                )
            )
        else:
            self.stdout.write(self.style.ERROR(f"Unknown vendor name {vendor_name}."))
