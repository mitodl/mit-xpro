"""
Course models
"""
import logging
import operator as op
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation

from courses.constants import (
    CATALOG_COURSE_IMG_WAGTAIL_FILL,
    COURSE_BG_IMG_WAGTAIL_FILL,
    COURSE_BG_IMG_MOBILE_WAGTAIL_FILL,
)
from courseware.utils import edx_redirect_url
from ecommerce.models import Product
from mitxpro.models import TimestampedModel, AuditableModel, AuditModel
from mitxpro.utils import now_in_utc, first_matching_item, serialize_model_object

User = get_user_model()

log = logging.getLogger(__name__)


class ProgramQuerySet(models.QuerySet):  # pylint: disable=missing-docstring
    def live(self):
        """Applies a filter for Programs with live=True"""
        return self.filter(live=True)


class ProgramManager(models.Manager):  # pylint: disable=missing-docstring
    def get_queryset(self):
        """Manager queryset"""
        return ProgramQuerySet(self.model, using=self._db)

    def live(self):
        """Returns a queryset of Programs with live=True"""
        return self.get_queryset().live()


class CourseQuerySet(models.QuerySet):  # pylint: disable=missing-docstring
    def live(self):
        """Applies a filter for Courses with live=True"""
        return self.filter(live=True)


class CourseManager(models.Manager):  # pylint: disable=missing-docstring
    def get_queryset(self):
        """Manager queryset"""
        return CourseQuerySet(self.model, using=self._db)

    def live(self):
        """Returns a queryset of Courses with live=True"""
        return self.get_queryset().live()


class PageProperties(models.Model):
    """
    Common properties for product pages
    """

    class Meta:
        abstract = True

    @property
    def background_image_url(self):
        """Gets the url for the background image (if that image exists)"""
        return (
            self.background_image.get_rendition(COURSE_BG_IMG_WAGTAIL_FILL).url
            if self.background_image
            else None
        )

    @property
    def background_image_mobile_url(self):
        """Gets the url for the background image (if that image exists)"""
        return (
            self.background_image.get_rendition(COURSE_BG_IMG_MOBILE_WAGTAIL_FILL).url
            if self.background_image
            else None
        )

    @property
    def catalog_image_url(self):
        """Gets the url for the thumbnail image as it appears in the catalog (if that image exists)"""
        return (
            self.page.thumbnail_image.get_rendition(CATALOG_COURSE_IMG_WAGTAIL_FILL).url
            if self.page and self.page.thumbnail_image
            else None
        )


class Program(TimestampedModel, PageProperties):
    """Model for a course program"""

    objects = ProgramManager()
    title = models.CharField(max_length=255)
    readable_id = models.CharField(null=True, max_length=255)
    live = models.BooleanField(default=False)
    products = GenericRelation(Product, related_query_name="programs")

    @property
    def page(self):
        """Gets the associated ProgramPage"""
        return getattr(self, "programpage", None)

    @property
    def num_courses(self):
        """Gets the number of courses in this program"""
        return self.courses.count()

    @property
    def next_run_date(self):
        """Gets the start date of the next CourseRun if one exists"""
        # NOTE: This is implemented with min() and courses.all() to allow for prefetch_related
        #   optimization. You can get the desired start_date with a filtered and sorted query, but
        #   that would run a new query even if prefetch_related was used.
        return min(
            filter(None, [course.next_run_date for course in self.courses.all()]),
            default=None,
        )

    @property
    def current_price(self):
        """Gets the price if it exists"""
        product = self.products.first()
        if not product:
            return None
        latest_version = product.latest_version
        if not latest_version:
            return None
        return latest_version.price

    @property
    def first_unexpired_run(self):
        """Gets the earliest unexpired CourseRun if one exists"""
        return min(
            filter(None, [course.first_unexpired_run for course in self.courses.all()]),
            default=None,
            key=lambda run: run.start_date,
        )

    def __str__(self):
        return self.title


class Course(TimestampedModel, PageProperties):
    """Model for a course"""

    objects = CourseManager()
    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, null=True, blank=True, related_name="courses"
    )
    position_in_program = models.PositiveSmallIntegerField(null=True, blank=True)
    title = models.CharField(max_length=255)
    readable_id = models.CharField(null=True, max_length=255)
    live = models.BooleanField(default=False)

    @property
    def page(self):
        """Gets the associated CoursePage"""
        return getattr(self, "coursepage", None)

    @property
    def next_run_date(self):
        """Gets the start date of the next CourseRun if one exists"""
        now = now_in_utc()
        # NOTE: This is implemented with min() and courseruns.all() to allow for prefetch_related
        #   optimization. You can get the desired start_date with a filtered and sorted query, but
        #   that would run a new query even if prefetch_related was used.
        return min(
            (
                course_run.start_date
                for course_run in self.courseruns.all()
                if course_run.start_date > now
            ),
            default=None,
        )

    @property
    def first_unexpired_run(self):
        """
        Gets the first unexpired CourseRun associated with this Course

        Returns:
            CourseRun or None: An unexpired course run
        """
        return first_matching_item(
            self.courseruns.all().order_by("start_date"),
            lambda course_run: course_run.is_unexpired,
        )

    @property
    def unexpired_runs(self):
        """
        Gets all the unexpired CourseRuns associated with this Course
        """
        return list(
            filter(
                op.attrgetter("is_unexpired"),
                self.courseruns.all().order_by("start_date"),
            )
        )

    def available_runs(self, user):
        """
        Get all enrollable runs for a Course that a user has not already enrolled in.

        Args:
            user (users.models.User): The user to check available runs for.

        Returns:
            list of CourseRun: Unexpired and unenrolled Course runs

        """
        enrolled_runs = user.courserunenrollment_set.filter(
            run__course=self
        ).values_list("run__id", flat=True)
        return [run for run in self.unexpired_runs if run.id not in enrolled_runs]

    class Meta:
        ordering = ("program", "title")

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        """Overridden save method"""
        # If adding a Course to a Program without position specified, set it as the highest position + 1.
        # WARNING: This is open to a race condition. Two near-simultaneous queries could end up with
        #    the same position_in_program value for multiple Courses in one Program. This is very
        #    unlikely (adding courses will be an admin-only task, and the position can be explicitly
        #    provided), easily fixed, and the resulting bug would be very minor.
        if self.program and not self.position_in_program:
            last_position = (
                self.program.courses.order_by("-position_in_program")
                .values_list("position_in_program", flat=True)
                .first()
            )
            self.position_in_program = 1 if not last_position else last_position + 1
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class CourseRun(TimestampedModel):
    """Model for a single run/instance of a course"""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="courseruns"
    )
    product = GenericRelation(Product, related_query_name="course_run")
    title = models.CharField(max_length=255)
    courseware_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    courseware_url_path = models.CharField(max_length=500, blank=True, null=True)
    start_date = models.DateTimeField(null=True, blank=True, db_index=True)
    end_date = models.DateTimeField(null=True, blank=True, db_index=True)
    enrollment_start = models.DateTimeField(null=True, blank=True, db_index=True)
    enrollment_end = models.DateTimeField(null=True, blank=True, db_index=True)
    live = models.BooleanField(default=False)
    products = GenericRelation(Product, related_query_name="courseruns")

    @property
    def is_past(self):
        """
        Checks if the course run in the past

        Returns:
            boolean: True if course run has ended

        """
        if not self.end_date:
            return False
        return self.end_date < now_in_utc()

    @property
    def is_not_beyond_enrollment(self):
        """
        Checks if the course is not beyond its enrollment period


        Returns:
            boolean: True if enrollment period has begun but not ended
        """
        now = now_in_utc()
        return (
            (self.end_date is None or self.end_date > now)
            and (self.enrollment_end is None or self.enrollment_end > now)
            and (self.enrollment_start is None or self.enrollment_start <= now)
        )

    @property
    def is_unexpired(self):
        """
        Checks if the course is not expired

        Returns:
            boolean: True if course is not expired
        """
        return not self.is_past and self.is_not_beyond_enrollment

    @property
    def courseware_url(self):
        """
        Full URL for this CourseRun as it exists in the courseware

        Returns:
            str or None: Full URL or None
        """
        return (
            edx_redirect_url(self.courseware_url_path)
            if self.courseware_url_path
            else None
        )

    @property
    def current_price(self):
        """Gets the price if it exists"""
        product = self.products.first()
        if not product:
            return None
        latest_version = product.latest_version
        if not latest_version:
            return None
        return latest_version.price

    def __str__(self):
        return self.title


class CourseRunEnrollment(TimestampedModel, AuditableModel):
    """
    Link between User and CourseRun indicating a user's enrollment
    """

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    run = models.ForeignKey("courses.CourseRun", on_delete=models.PROTECT)
    company = models.ForeignKey(
        "ecommerce.Company", null=True, on_delete=models.PROTECT
    )
    edx_enrolled = models.BooleanField(
        default=False,
        help_text="Indicates whether or not the request succeeded to enroll via the edX API",
    )
    active = models.BooleanField(
        default=True,
        help_text="Indicates whether or not this enrollment should be considered active",
    )

    class Meta:
        unique_together = ("user", "run")

    @classmethod
    def get_audit_class(cls):
        return CourseRunEnrollmentAudit

    def to_dict(self):
        return serialize_model_object(self)

    def __str__(self):
        return f"CourseRunEnrollment for {self.user} and {self.run}"


class CourseRunEnrollmentAudit(AuditModel):
    """Audit table for CourseRunEnrollment"""

    enrollment = models.ForeignKey(
        CourseRunEnrollment, null=True, on_delete=models.PROTECT
    )

    @classmethod
    def get_related_field_name(cls):
        return "enrollment"


class ProgramEnrollment(TimestampedModel, AuditableModel):
    """
    Link between User and Program indicating a user's enrollment
    """

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    program = models.ForeignKey("courses.Program", on_delete=models.PROTECT)
    company = models.ForeignKey(
        "ecommerce.Company", null=True, on_delete=models.PROTECT
    )
    active = models.BooleanField(
        default=True,
        help_text="Indicates whether or not this enrollment should be considered active",
    )

    class Meta:
        unique_together = ("user", "program")

    @classmethod
    def get_audit_class(cls):
        return ProgramEnrollmentAudit

    def to_dict(self):
        return serialize_model_object(self)

    def __str__(self):
        return f"ProgramEnrollment for {self.user} and {self.program}"


class ProgramEnrollmentAudit(AuditModel):
    """Audit table for ProgramEnrollment"""

    enrollment = models.ForeignKey(
        ProgramEnrollment, null=True, on_delete=models.PROTECT
    )

    @classmethod
    def get_related_field_name(cls):
        return "enrollment"
