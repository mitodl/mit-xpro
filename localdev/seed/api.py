"""Functions/classes for adding and removing seed data"""
import os
import json
from types import SimpleNamespace
from collections import defaultdict, namedtuple
from wagtail.core.models import Page

from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from courses.models import (
    Program,
    Course,
    CourseRun,
    CourseRunEnrollment,
    CourseRunEnrollmentAudit,
    CourseTopic,
    ProgramEnrollment,
    ProgramEnrollmentAudit,
)
from localdev.seed.serializers import (
    ProgramSerializer,
    CourseSerializer,
    CourseRunSerializer,
)
from mitxpro.utils import (
    dict_without_keys,
    filter_dict_by_key_set,
    get_field_names,
    first_or_none,
    has_equal_properties,
)
from cms.models import (
    ProgramPage,
    CoursePage,
    ResourcePage,
    CourseIndexPage,
    ProgramIndexPage,
)
from cms.utils import get_home_page
from ecommerce.models import (
    Product,
    ProductVersion,
    CouponEligibility,
    CouponSelection,
    CouponRedemption,
    Order,
    OrderAudit,
    Line,
    Receipt,
    Basket,
    BasketItem,
    CourseRunSelection,
    ProductCouponAssignment,
)

# ROUGH EXPECTED FORMAT FOR SEED DATA FILE:
# {
#     "programs": [
#         {
#             ...mixed Program and ProgramPage properties...
#             ...optional "_product" key pointing to dict of ProductVersion properties...
#         }
#     ],
#     "courses": [
#         {
#             ...optional "program" key pointing to a parent Program title...
#             ...mixed Course and CoursePage properties...
#             "course_runs": [
#                 ...CourseRun properties...
#                 ...optional "_product" key pointing to dict of ProductVersion properties...
#             ]
#         }
#     ],
#     "resource_pages": [
#         {
#             ...ResourcePage properties...
#         }
#     ],
#     "topics": [
#         {"name": "cars"}
#     ]
# }


SEED_DATA_FILE_PATH = os.path.join(
    settings.BASE_DIR, "localdev/seed/resources/seed_data.json"
)


def get_raw_seed_data_from_file():
    """Loads raw seed data from our seed data file"""
    with open(SEED_DATA_FILE_PATH) as f:
        return json.loads(f.read())


def get_courseware_page_parent(courseware_page_obj):
    """Gets an instance of the parent index/listing page for a CoursePage/ProgramPage"""
    if isinstance(courseware_page_obj, Course):
        index_page_cls = CourseIndexPage
    elif isinstance(courseware_page_obj, Program):
        index_page_cls = ProgramIndexPage
    else:
        return None
    page_specific = Page.objects.get(id=index_page_cls.objects.first().id).specific
    return page_specific


def delete_wagtail_pages(page_cls, filter_dict):
    """
    Completely deletes Wagtail CMS pages that match a filter. Wagtail overrides standard delete functionality,
    making it difficult to actually delete Page objects and get information about what was deleted.
    """
    page_ids_to_delete = (
        page_cls.objects.filter(**filter_dict).values_list("id", flat=True).all()
    )
    num_pages = len(page_ids_to_delete)
    base_pages_qset = Page.objects.filter(id__in=page_ids_to_delete)
    if not base_pages_qset.exists():
        return 0, {}
    base_pages_qset.delete()
    return (
        num_pages,
        {page_cls._meta.label: num_pages},  # pylint: disable=protected-access
    )


def filter_for_model_fields(model_cls, dict_to_filter):
    """Filters a dict to return only the keys that match fields in a model class"""
    model_field_names = get_field_names(model_cls)
    return filter_dict_by_key_set(dict_to_filter, model_field_names)


def set_model_properties_from_dict(model_obj, property_dict):
    """
    Takes a model object and a dict property names mapped to desired values, then sets all of the relevant
    property values on the model object and saves it
    """
    for field, value in property_dict.items():
        setattr(model_obj, field, value)
    model_obj.save()
    return model_obj


SeedDataSpec = namedtuple("SeedDataSpec", ["model_cls", "data", "parent"])


class SeedResult:
    """Represents the results of seeding/unseeding"""

    def __init__(self):
        self.created = defaultdict(int)
        self.updated = defaultdict(int)
        self.deleted = defaultdict(int)
        self.ignored = defaultdict(int)

    def add_created(self, obj):
        """Adds to the count of created object types"""
        self.created[obj.__class__.__name__] += 1

    def add_updated(self, obj):
        """Adds to the count of updated object types"""
        self.updated[obj.__class__.__name__] += 1

    def add_ignored(self, obj):
        """Adds to the count of ignored object types"""
        self.ignored[obj.__class__.__name__] += 1

    def add_deleted(self, deleted_type_dict):
        """Adds to the count of deleted object types"""
        for deleted_type, deleted_count in deleted_type_dict.items():
            if deleted_count:
                self.deleted[deleted_type] += deleted_count

    @property
    def report(self):
        """Simple dict representing the seed result"""
        return {
            "Created": dict(self.created),
            "Updated": dict(self.updated),
            "Deleted": dict(self.deleted),
            "Ignored (Already Existed)": dict(self.ignored),
        }

    def __repr__(self):
        return str(self.report)


class SeedDataLoader:
    """Handles creation/updating/deletion of seed data based on raw data"""

    # Our legacy course models did not enforce uniqueness on any fields. It's possible that
    # we'll want to change that, but for now this dict exists to indicate which field should
    # be used to (a) find an existing object for some data we're deserializing, and
    # (b) prepend a string indicating that the object is seed data.
    SEED_DATA_FIELD_MAP = {Program: "title", Course: "title", CourseRun: "title"}
    SEED_DATA_DESERIALIZER = {
        Program: ProgramSerializer,
        Course: CourseSerializer,
        CourseRun: CourseRunSerializer,
    }
    # Maps a course model with some information about its associated Wagtail page class
    COURSE_MODEL_PAGE_PROPS = {
        Program: SimpleNamespace(
            page_cls=ProgramPage, page_field_name=ProgramPage.program.field.name
        ),
        Course: SimpleNamespace(
            page_cls=CoursePage, page_field_name=CoursePage.course.field.name
        ),
    }
    ECOMMERCE_TYPES = {CourseRun, Program}
    # String to prepend to a field value that will indicate seed data.
    SEED_DATA_PREFIX = "SEED"

    def __init__(self):
        self.seed_result = SeedResult()

    @classmethod
    def seed_prefixed(cls, value):
        """Returns the same value with a prefix that indicates seed data"""
        return " ".join([cls.SEED_DATA_PREFIX, value])

    @classmethod
    def is_seed_value(cls, value):
        """Returns True of the given value matches the seeded value format"""
        return value.startswith("{} ".format(cls.SEED_DATA_PREFIX))

    def _seeded_field_and_value(self, model_cls, data):
        """
        Returns the field name and seed-adjusted value for some data that is being deserialized on some model

        Example return value: ("title", "SEED My Course Title")
        """
        field_name = self.SEED_DATA_FIELD_MAP[model_cls]
        seeded_value = self.seed_prefixed(data[field_name])
        return field_name, seeded_value

    def _get_existing_seeded_qset(self, model_cls, data):
        """Returns a qset of seed data objects for some model class"""
        field_name, seeded_value = self._seeded_field_and_value(model_cls, data)
        return model_cls.objects.filter(**{field_name: seeded_value})

    def _deserialize(self, serializer_cls, data):
        """
        Attempts to deserialize and save a courseware object (Program/Course/CourseRun),
        and creates it if it doesn't exist.
        """
        model_cls = serializer_cls.Meta.model
        field_name, seeded_value = self._seeded_field_and_value(model_cls, data)
        model_object_data = {
            # Set 'live' to True for seeded objects by default
            "live": True,
            # Use every property in 'data' that corresponds to a model property
            **filter_for_model_fields(model_cls, data),
            # Use the seed-adjusted value for the property that we're using to identify seeded objects
            field_name: seeded_value,
        }
        topics = None
        if model_cls == Course and "topics" in model_object_data:
            topics = model_object_data.pop("topics")
        existing_qset = self._get_existing_seeded_qset(model_cls, data)
        if existing_qset.exists():
            existing_qset.update(**model_object_data)
            courseware_obj = existing_qset.first()
            self.seed_result.add_updated(courseware_obj)
        else:
            serialized = serializer_cls(data=model_object_data)
            serialized.is_valid(raise_exception=True)
            courseware_obj = serialized.save()
            self.seed_result.add_created(courseware_obj)
        if topics is not None:
            topic_objs = [
                CourseTopic.objects.get_or_create(name=topic["name"])[0]
                for topic in topics
            ]
            courseware_obj.topics.set(topic_objs)
        return courseware_obj

    def _deserialize_product(self, courseware_obj, product_data):
        """
        Attempts to deserialize and save Product/ProductVersion data, and creates those objects if they don't exist.
        """
        product, created = Product.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(courseware_obj.__class__),
            object_id=courseware_obj.id,
        )
        if created:
            self.seed_result.add_created(product)
        latest_version = product.latest_version
        if not latest_version or not has_equal_properties(latest_version, product_data):
            new_version = ProductVersion.objects.create(product=product, **product_data)
            self.seed_result.add_created(new_version)
            return new_version
        else:
            self.seed_result.add_ignored(latest_version)
            return latest_version

    def _deserialize_courseware_cms_page(self, courseware_obj, data):
        """
        Attempts to deserialize and save a Wagtail CMS page for some Program/Course,
        and creates one if one doesn't exist
        """
        model_cls = courseware_obj.__class__
        cms_page_props = self.COURSE_MODEL_PAGE_PROPS[model_cls]
        cms_page_cls = cms_page_props.page_cls
        cms_page_field_name = cms_page_props.page_field_name
        # Build a queryset for any existing CMS pages for this Program/Course
        existing_page_qset = cms_page_cls.objects.filter(
            **{cms_page_field_name: courseware_obj}
        )
        # CMS pages have a title property as well. Use the seed-adjusted value for it
        field_name, seeded_value = self._seeded_field_and_value(model_cls, data)
        cms_model_data = {
            cms_page_field_name: courseware_obj,
            **filter_for_model_fields(cms_page_cls, data),
            field_name: seeded_value,
        }
        if existing_page_qset.exists():
            existing_page_qset.update(**cms_model_data)
            existing_page = existing_page_qset.first()
            self.seed_result.add_updated(existing_page)
            return existing_page
        else:
            page_obj = cms_page_cls(**cms_model_data)
            courseware_page_parent = get_courseware_page_parent(courseware_obj)
            courseware_page_parent.add_child(instance=page_obj)
            page_obj.save()
            self.seed_result.add_created(page_obj)
            return page_obj

    def _deserialize_cms_resource_page(self, resource_page_data):
        """Create/update Wagtail resource pages."""
        existing_page_qset = ResourcePage.objects.filter(
            title=resource_page_data["title"]
        )
        page_data = {
            **filter_for_model_fields(ResourcePage, resource_page_data),
            "content": json.dumps(resource_page_data["content"]),
        }
        if existing_page_qset.exists():
            existing_page = existing_page_qset.first()
            existing_page = set_model_properties_from_dict(existing_page, page_data)
            self.seed_result.add_updated(existing_page)
            return existing_page
        else:
            page_obj = ResourcePage(**page_data)
            added_obj = get_home_page().add_child(instance=page_obj)
            self.seed_result.add_created(added_obj)
            return added_obj

    def _delete_courseware_cms_page(self, courseware_obj, cms_page_props):
        """Deletes a Wagtail page associated with a given Program/Course"""
        cms_page_cls = cms_page_props.page_cls
        cms_page_field_name = cms_page_props.page_field_name
        deleted_count, deleted_type_counts = delete_wagtail_pages(
            cms_page_cls, {cms_page_field_name: courseware_obj}
        )
        self.seed_result.add_deleted(deleted_type_counts)
        return deleted_count, deleted_type_counts

    def _delete_ecommerce_for_courseware_obj(self, courseware_obj):
        """
        Deletes all relevant ecommerce objects associated with a given Program/CourseRun. This specialized, ordered
        deletion is necessary because our ecommerce tables have delete protection.
        """
        # First, delete enrollments
        if courseware_obj.__class__ == CourseRun:
            enrollment_audit_qset = CourseRunEnrollmentAudit.objects.filter(
                enrollment__run=courseware_obj
            )
            enrollment_qset = CourseRunEnrollment.all_objects.filter(run=courseware_obj)
        else:
            enrollment_audit_qset = ProgramEnrollmentAudit.objects.filter(
                enrollment__program=courseware_obj
            )
            enrollment_qset = ProgramEnrollment.all_objects.filter(
                program=courseware_obj
            )
        delete_results = [enrollment_audit_qset.delete(), enrollment_qset.delete()]

        # Then, delete ecommerce objects that are associated with the product (if a product
        # exists for this course run/program)
        content_type = ContentType.objects.get_for_model(courseware_obj.__class__)
        product_ids = Product.objects.filter(
            content_type=content_type, object_id=courseware_obj.id
        ).values_list("id", flat=True)

        if len(product_ids) > 0:
            lines = Line.objects.filter(product_version__product_id__in=product_ids)
            order_ids = {line.order_id for line in lines}
            basket_ids = BasketItem.objects.filter(
                product_id__in=product_ids
            ).values_list("basket__id", flat=True)
            delete_results.extend(
                [
                    CourseRunSelection.objects.filter(
                        basket_id__in=basket_ids
                    ).delete(),
                    CouponSelection.objects.filter(basket_id__in=basket_ids).delete(),
                    BasketItem.objects.filter(basket_id__in=basket_ids).delete(),
                    Basket.objects.filter(id__in=basket_ids).delete(),
                    Line.objects.filter(id__in=[line.id for line in lines]).delete(),
                    CouponRedemption.objects.filter(order_id__in=order_ids).delete(),
                    Receipt.objects.filter(order_id__in=order_ids).delete(),
                    OrderAudit.objects.filter(order_id__in=order_ids).delete(),
                    Order.objects.filter(id__in=order_ids).delete(),
                    ProductCouponAssignment.objects.filter(
                        product_coupon__product_id__in=product_ids
                    ).delete(),
                    CouponEligibility.objects.filter(
                        product_id__in=product_ids
                    ).delete(),
                    ProductVersion.objects.filter(product__id__in=product_ids).delete(),
                    Product.objects.filter(id__in=product_ids).delete(),
                ]
            )

        for _, deleted_type_dict in delete_results:
            self.seed_result.add_deleted(deleted_type_dict)

    def _delete_cms_resource_page(self, resource_page):
        """Delete Wagtail resource pages."""
        existing_obj = ResourcePage.objects.filter(title=resource_page["title"]).first()
        if not existing_obj:
            return 0, {}
        __, deleted_type_counts = delete_wagtail_pages(
            ResourcePage, {"id": existing_obj.id}
        )
        self.seed_result.add_deleted(deleted_type_counts)

    def iter_seed_data(self, raw_data):
        """
        Iterate through raw seed data and yields the specification for models that will be created/updated/deleted
        """
        for raw_program_data in raw_data["programs"]:
            yield SeedDataSpec(model_cls=Program, data=raw_program_data, parent=None)

        for raw_course_data in raw_data["courses"]:
            program_title = raw_course_data.get("program")
            program_id = (
                first_or_none(
                    Program.objects.filter(
                        title=self.seed_prefixed(program_title)
                    ).values_list("id", flat=True)
                )
                if program_title
                else None
            )
            course_runs_data = raw_course_data.get("course_runs", [])
            course_spec = SeedDataSpec(
                model_cls=Course,
                data={
                    # The deserializer (or Django) will think "course_runs" has CourseRun objects,
                    # so it has to be excluded
                    **dict_without_keys(raw_course_data, "course_runs"),
                    "program": program_id,
                },
                parent=None,
            )
            yield course_spec

            course_title = raw_course_data["title"]
            course_id = first_or_none(
                Course.objects.filter(
                    title=self.seed_prefixed(course_title)
                ).values_list("id", flat=True)
            )
            for raw_course_run_data in course_runs_data:
                yield SeedDataSpec(
                    model_cls=CourseRun,
                    data={**raw_course_run_data, "course": course_id},
                    parent=course_spec,
                )

        for resource_page_data in raw_data["resource_pages"]:
            yield SeedDataSpec(
                model_cls=ResourcePage, data=resource_page_data, parent=None
            )

    def create_seed_data(self, raw_data):
        """
        Iterate over all objects described in the seed data spec, add/update them one-by-one, and return the results
        """
        self.seed_result = SeedResult()
        for seed_data_spec in self.iter_seed_data(raw_data):
            if seed_data_spec.model_cls in [Program, Course, CourseRun]:
                serializer_cls = self.SEED_DATA_DESERIALIZER[seed_data_spec.model_cls]
                courseware_model_obj = self._deserialize(
                    serializer_cls, seed_data_spec.data
                )
                if seed_data_spec.model_cls in self.COURSE_MODEL_PAGE_PROPS:
                    self._deserialize_courseware_cms_page(
                        courseware_model_obj, seed_data_spec.data
                    )
                if "_product" in seed_data_spec.data:
                    self._deserialize_product(
                        courseware_model_obj, seed_data_spec.data["_product"]
                    )
            elif seed_data_spec.model_cls == ResourcePage:
                self._deserialize_cms_resource_page(seed_data_spec.data)
        return self.seed_result

    def delete_courseware_obj(self, courseware_obj):
        """
        Attempts to delete a seeded Program/Course/CourseRun and associated objects
        """
        # If there are any Wagtail pages associated with this Program/Course, delete them.
        cms_page_props = self.COURSE_MODEL_PAGE_PROPS.get(courseware_obj.__class__)
        if cms_page_props:
            self._delete_courseware_cms_page(courseware_obj, cms_page_props)
        if courseware_obj.__class__ in self.ECOMMERCE_TYPES:
            # If there are ecommerce objects associated with this Program/CourseRun, delete them
            self._delete_ecommerce_for_courseware_obj(courseware_obj)

        deleted_count, deleted_type_counts = courseware_obj.delete()
        self.seed_result.add_deleted(deleted_type_counts)
        return deleted_count, deleted_type_counts

    def delete_seed_data(self, raw_data):
        """Iterate over all objects described in the seed data spec, delete them one-by-one, and return the results"""
        self.seed_result = SeedResult()
        # Traversing in reverse since we want to delete 'leaf' objects first (e.g.: we want to delete CourseRuns
        # before deleting Courses)
        for seed_data_spec in reversed(list(self.iter_seed_data(raw_data))):
            if seed_data_spec.model_cls in [Program, Course, CourseRun]:
                existing_qset = self._get_existing_seeded_qset(
                    seed_data_spec.model_cls, seed_data_spec.data
                )
                if not existing_qset.exists():
                    continue
                self.delete_courseware_obj(existing_qset.first())
            elif seed_data_spec.model_cls == ResourcePage:
                self._delete_cms_resource_page(seed_data_spec.data)
        return self.seed_result
