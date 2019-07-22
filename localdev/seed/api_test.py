"""Seed data API tests"""
# pylint: disable=unused-argument, redefined-outer-name
from types import SimpleNamespace
import pytest

from courses.models import Program, Course, CourseRun
from cms.models import ProgramPage, CoursePage, ResourcePage
from ecommerce.models import Product, ProductVersion
from ecommerce.test_utils import unprotect_version_tables
from localdev.seed.api import SeedDataLoader, get_raw_seed_data_from_file


@pytest.fixture
def seeded():
    """Fixture for a scenario where course data has been loaded from our JSON file"""
    data = get_raw_seed_data_from_file()
    seed_data_loader = SeedDataLoader()
    seed_data_loader.create_seed_data(data)
    return SimpleNamespace(raw_data=data, loader=seed_data_loader)


@pytest.mark.django_db
def test_seed_prefix(seeded):
    """
    Tests that the seed data functions add a prefix to a field values that indicates which objects are seed data
    """
    # Test helper functions
    seeded_value = seeded.loader.seed_prefixed("Some Title")
    assert seeded_value == "{} Some Title".format(SeedDataLoader.SEED_DATA_PREFIX)
    assert seeded.loader.is_seed_value(seeded_value) is True
    # Test saved object titles
    assert (
        Program.objects.exclude(
            title__startswith=SeedDataLoader.SEED_DATA_PREFIX
        ).exists()
        is False
    )
    assert (
        Course.objects.exclude(
            title__startswith=SeedDataLoader.SEED_DATA_PREFIX
        ).exists()
        is False
    )
    assert (
        CourseRun.objects.exclude(
            title__startswith=SeedDataLoader.SEED_DATA_PREFIX
        ).exists()
        is False
    )


@pytest.mark.django_db
def test_seed_and_unseed_data(seeded):
    """Tests that the seed data functions can create and delete seed data"""
    expected_programs = len(seeded.raw_data["programs"])
    expected_courses = len(seeded.raw_data["courses"])
    expected_course_runs = sum(
        len(course_data.get("course_runs", []))
        for course_data in seeded.raw_data["courses"]
    )
    # Hardcoding this value since it would be annoying to check for it programatically
    expected_products = 7
    expected_resource_pages = len(seeded.raw_data["resource_pages"])
    assert Program.objects.count() == expected_programs
    assert ProgramPage.objects.count() == expected_programs
    assert Course.objects.count() == expected_courses
    assert CoursePage.objects.count() == expected_courses
    assert CourseRun.objects.count() == expected_course_runs
    assert ResourcePage.objects.count() == expected_resource_pages
    assert Product.objects.count() == expected_products
    assert ProductVersion.objects.count() == expected_products

    with unprotect_version_tables():
        seeded.loader.delete_seed_data(seeded.raw_data)
    assert Program.objects.count() == 0
    assert ProgramPage.objects.count() == 0
    assert Course.objects.count() == 0
    assert CoursePage.objects.count() == 0
    assert CourseRun.objects.count() == 0
    assert ResourcePage.objects.count() == 0
    assert Product.objects.count() == 0
    assert ProductVersion.objects.count() == 0
