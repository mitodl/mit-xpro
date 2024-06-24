"""
Sync external course API tests
"""

import json
import logging
import random
from pathlib import Path

import pytest

from cms.factories import (
    CourseIndexPageFactory,
    ExternalCoursePageFactory,
    HomePageFactory,
)
from courses.factories import CourseFactory, CourseRunFactory, PlatformFactory
from courses.models import Course
from courses.sync_external_courses.emeritus_api import (
    EmeritusCourse,
    EmeritusKeyMap,
    create_learning_outcomes_page,
    create_or_update_emeritus_course_page,
    create_or_update_emeritus_course_run,
    create_who_should_enroll_in_page,
    fetch_emeritus_courses,
    generate_emeritus_course_run_tag,
    generate_external_course_run_courseware_id,
    parse_emeritus_data_str,
    update_emeritus_course_runs,
)
from mitxpro.test_utils import MockResponse
from mitxpro.utils import clean_url


@pytest.mark.parametrize(
    ("emeritus_course_run_code", "expected_course_run_tag"),
    [
        ("MO-EOB-18-01#1", "18-01#1"),
        ("MO-EOB-08-01#1", "08-01#1"),
        ("MO-EOB-08-12#1", "08-12#1"),
        ("MO-EOB-18-01#12", "18-01#12"),
        ("MO-EOB-18-01#212", "18-01#212"),
    ],
)
def test_generate_emeritus_course_run_tag(
    emeritus_course_run_code, expected_course_run_tag
):
    """
    Tests that `generate_emeritus_course_run_tag` generates the expected course tag for Emeritus Course Run Codes.
    """
    assert (
        generate_emeritus_course_run_tag(emeritus_course_run_code)
        == expected_course_run_tag
    )


@pytest.mark.parametrize(
    ("course_readable_id", "course_run_tag", "expected_course_run_courseware_id"),
    [
        ("course-v1:xPRO+EOB", "18-01#1", "course-v1:xPRO+EOB+18-01#1"),
        ("course-v1:xPRO+EOB", "08-01#1", "course-v1:xPRO+EOB+08-01#1"),
        ("course-v1:xPRO+EOB", "18-01#12", "course-v1:xPRO+EOB+18-01#12"),
        ("course-v1:xPRO+EOB", "18-01#212", "course-v1:xPRO+EOB+18-01#212"),
    ],
)
def test_generate_external_course_run_courseware_id(
    course_readable_id, course_run_tag, expected_course_run_courseware_id
):
    """
    Test that `generate_external_course_run_courseware_id` returns the expected courseware_id for the given
    course run tag and course readable id.
    """
    assert (
        generate_external_course_run_courseware_id(course_run_tag, course_readable_id)
        == expected_course_run_courseware_id
    )


@pytest.mark.parametrize("create_course_page", [True, False])
@pytest.mark.django_db
def test_create_or_update_emeritus_course_page(create_course_page):
    """
    Test that `create_or_update_emeritus_course_page` creates a new course or updates the existing.
    """
    home_page = HomePageFactory.create(title="Home Page", subhead="<p>subhead</p>")
    course_index_page = CourseIndexPageFactory.create(parent=home_page, title="Courses")
    course = CourseFactory.create()

    emeritus_course_run = {
        "program_name": "Internet of Things (IoT): Design and Applications",
        "course_code": "MO-DBIP",
        "course_run_code": "MO-DBIP.ELE-25-07#1",
        "start_date": "2025-07-30",
        "end_date": "2025-09-24",
        "Category": "Technology",
        "list_price": 2600,
        "list_currency": "USD",
        "total_weeks": 7,
        "product_family": "Certificate",
        "product_sub_type": "Short Form",
        "format": "Online",
        "suggested_duration": 49,
        "language": "English",
        "landing_page_url": "https://emeritus-api.io/Internet-of-things-iot-design-and-applications"
        "?utm_medium=EmWebsite&utm_campaign=direct_EmWebsite?utm_campaign=school_website&utm_medium"
        "=website&utm_source=MIT-web",
        "Apply_now_url": "https://emeritus-api.io/?locale=en&program_sfid=01t2s000000OHA2AAO&source"
        "=applynowlp&utm_campaign=school&utm_medium=MITWebsite&utm_source=MIT-web",
        "description": "Test Description",
        "learning_outcomes": None,
        "program_for": None,
    }

    if create_course_page:
        ExternalCoursePageFactory.create(
            course=course,
            title=emeritus_course_run["program_name"],
            external_marketing_url="",
            duration="",
            description="",
        )

    course_page = create_or_update_emeritus_course_page(
        course_index_page, course, EmeritusCourse(emeritus_course_run)
    )
    assert course_page.title == emeritus_course_run["program_name"]
    assert course_page.external_marketing_url == clean_url(
        emeritus_course_run["landing_page_url"], remove_query_params=True
    )
    assert course_page.course == course
    assert course_page.duration == f"{emeritus_course_run['total_weeks']} Weeks"
    assert course_page.description == emeritus_course_run["description"]


@pytest.mark.django_db
def test_create_who_should_enroll_in_page():
    """
    Tests that `create_who_should_enroll_in_page` creates the `WhoShouldEnrollPage`.
    """
    course_page = ExternalCoursePageFactory.create()
    who_should_enroll_str = (
        "The program is ideal for:\r\n●       Early-career IT professionals, network engineers, "
        "and system administrators wanting to gain a comprehensive overview of cybersecurity and "
        "fast-track their career progression\r\n●       IT project managers and engineers keen on "
        "gaining the ability to think critically about the threat landscape, including "
        "vulnerabilities in cybersecurity, and upgrading their resume for career "
        "advancement\r\n●       Mid- or later-career professionals seeking a career change and "
        "looking to add critical cybersecurity knowledge and foundational lessons to their resume"
    )
    create_who_should_enroll_in_page(
        course_page, parse_emeritus_data_str(who_should_enroll_str)
    )
    assert parse_emeritus_data_str(who_should_enroll_str) == [
        item.value.source for item in course_page.who_should_enroll.content
    ]
    assert course_page.who_should_enroll is not None


@pytest.mark.django_db
def test_create_learning_outcomes_page():
    """
    Tests that `create_learning_outcomes_page` creates the `LearningOutcomesPage`.
    """
    course_page = ExternalCoursePageFactory.create()
    learning_outcomes_str = (
        "This program will enable you to:\r\n●       Gain an overview of cybersecurity risk "
        "management, including its foundational concepts and relevant regulations\r\n●       "
        "Explore the domains covering various aspects of cloud technology\r\n●       "
        "Learn adversary tactics and techniques that are utilized as the foundational development "
        "of specific threat models and methodologies\r\n●       Understand the guidelines for "
        "organizations to prepare themselves against cybersecurity attacks"
    )
    create_learning_outcomes_page(
        course_page, parse_emeritus_data_str(learning_outcomes_str)
    )
    assert parse_emeritus_data_str(learning_outcomes_str) == [
        item.value for item in course_page.outcomes.outcome_items
    ]
    assert course_page.outcomes is not None


def test_parse_emeritus_data_str():
    """
    Tests that `parse_emeritus_data_str` parses who should enroll and learning outcomes strings as expected.
    """
    data_str = (
        "This program will enable you to:\r\n●       Gain an overview of cybersecurity risk "
        "management, including its foundational concepts and relevant regulations\r\n●       "
        "Explore the domains covering various aspects of cloud technology\r\n●       "
        "Learn adversary tactics and techniques that are utilized as the foundational development "
        "of specific threat models and methodologies\r\n●       Understand the guidelines for "
        "organizations to prepare themselves against cybersecurity attacks"
    )
    assert parse_emeritus_data_str(data_str) == [
        "Gain an overview of cybersecurity risk management, including "
        "its foundational concepts and relevant regulations",
        "Explore the domains covering various aspects of cloud technology",
        "Learn adversary tactics and techniques that are utilized as the foundational development "
        "of specific threat models and methodologies",
        "Understand the guidelines for organizations to prepare themselves against cybersecurity attacks",
    ]


@pytest.mark.parametrize("create_existing_course_run", [True, False])
@pytest.mark.django_db
def test_create_or_update_emeritus_course_run(create_existing_course_run):
    """
    Tests that `create_or_update_emeritus_course_run` creates or updates a course run
    """
    with Path(
        "courses/sync_external_courses/test_data/batch_test.json"
    ).open() as test_data_file:
        emeritus_course = EmeritusCourse(json.load(test_data_file)["rows"][0])

    course = CourseFactory.create()
    if create_existing_course_run:
        CourseRunFactory.create(
            course=course,
            external_course_run_id=emeritus_course.course_run_code,
            enrollment_start=None,
            enrollment_end=None,
            expiration_date=None,
        )

    create_or_update_emeritus_course_run(course, emeritus_course)
    course_runs = course.courseruns.all()
    course_run_courseware_id = generate_external_course_run_courseware_id(
        emeritus_course.course_run_tag, course.readable_id
    )

    assert len(course_runs) == 1
    if create_existing_course_run:
        expected_data = {
            "external_course_run_id": emeritus_course.course_run_code,
            "start_date": emeritus_course.start_date,
            "end_date": emeritus_course.end_date,
        }
    else:
        expected_data = {
            "title": emeritus_course.course_title,
            "external_course_run_id": emeritus_course.course_run_code,
            "courseware_id": course_run_courseware_id,
            "run_tag": emeritus_course.course_run_tag,
            "start_date": emeritus_course.start_date,
            "end_date": emeritus_course.end_date,
            "live": True,
        }
    for attr_name, expected_value in expected_data.items():
        assert getattr(course_runs[0], attr_name) == expected_value


@pytest.mark.parametrize("create_existing_course_runs", [True, False])
@pytest.mark.django_db
def test_update_emeritus_course_runs(create_existing_course_runs):
    """
    Tests that `update_emeritus_course_runs` creates new courses and updates existing.
    """
    with Path(
        "courses/sync_external_courses/test_data/batch_test.json"
    ).open() as test_data_file:
        emeritus_course_runs = json.load(test_data_file)["rows"]

    platform = PlatformFactory.create(name=EmeritusKeyMap.PLATFORM_NAME.value)

    if create_existing_course_runs:
        for run in random.sample(emeritus_course_runs, len(emeritus_course_runs) // 2):
            course = CourseFactory.create(
                title=run["program_name"],
                platform=platform,
                external_course_id=run["course_code"],
                is_external=True,
            )
            CourseRunFactory.create(
                course=course,
                external_course_run_id=run["course_run_code"],
                enrollment_start=None,
                enrollment_end=None,
                expiration_date=None,
            )

            home_page = HomePageFactory.create(
                title="Home Page", subhead="<p>subhead</p>"
            )
            CourseIndexPageFactory.create(parent=home_page, title="Courses")
            ExternalCoursePageFactory.create(
                course=course,
                title=run["program_name"],
                external_marketing_url="",
                duration="",
                description="",
            )

    update_emeritus_course_runs(emeritus_course_runs)
    courses = Course.objects.filter(platform=platform)
    assert len(courses) == len(emeritus_course_runs)
    for emeritus_course_run in emeritus_course_runs:
        course = Course.objects.filter(
            platform=platform,
            external_course_id=emeritus_course_run["course_code"],
            is_external=True,
        ).first()
        assert course is not None
        assert (
            course.courseruns.filter(
                external_course_run_id=emeritus_course_run["course_run_code"]
            ).count()
            == 1
        )
        assert hasattr(course, "externalcoursepage")

        course_page = course.externalcoursepage
        if emeritus_course_run["program_for"]:
            assert course_page.who_should_enroll is not None
        if emeritus_course_run["learning_outcomes"]:
            assert course_page.outcomes is not None


def test_fetch_emeritus_courses_success(settings, mocker):
    """
    Tests that `fetch_emeritus_courses` makes the required calls to the `Emeritus` API. Tests the success scenario.

    Here is the expected flow:
        1. Make a get request to get a list of reports.
        2. Make a post request for the `Batch` report.
        3. If the results are not ready, wait for the job to complete and make a get request to check the status.
        4. If the results are ready after the post request, return the results.
        5. If job status is 1 or 2, it is in progress. Wait for 2 seconds and make a get request for Job status.
        6. If job status is 3, the results are ready, make a get request to collect the results and return the data.
    """
    settings.EMERITUS_API_BASE_URL = "https://test_emeritus_api.io"
    settings.EMERITUS_API_KEY = "test_emeritus_api_key"
    settings.EMERITUS_API_REQUEST_TIMEOUT = 60

    mock_get = mocker.patch(
        "courses.sync_external_courses.emeritus_api_client.requests.get"
    )
    mock_post = mocker.patch(
        "courses.sync_external_courses.emeritus_api_client.requests.post"
    )

    with Path(
        "courses/sync_external_courses/test_data/batch_test.json"
    ).open() as test_data_file:
        emeritus_course_runs = json.load(test_data_file)

    batch_query = {
        "id": 77,
        "name": "Batch",
    }
    mock_get.side_effect = [
        MockResponse({"results": [batch_query]}),
        MockResponse({"job": {"status": 1}}),
        MockResponse({"job": {"status": 2}}),
        MockResponse({"job": {"status": 3, "query_result_id": 1}}),
        MockResponse({"query_result": {"data": emeritus_course_runs}}),
    ]
    mock_post.side_effect = [MockResponse({"job": {"id": 1}})]

    actual_course_runs = fetch_emeritus_courses()

    mock_get.assert_any_call(
        "https://test_emeritus_api.io/api/queries?api_key=test_emeritus_api_key",
        timeout=60,
    )
    mock_post.assert_called_once()
    mock_get.assert_any_call(
        "https://test_emeritus_api.io/api/jobs/1?api_key=test_emeritus_api_key",
        timeout=60,
    )
    mock_get.assert_any_call(
        "https://test_emeritus_api.io/api/query_results/1?api_key=test_emeritus_api_key",
        timeout=60,
    )
    assert actual_course_runs == emeritus_course_runs["rows"]


def test_fetch_emeritus_courses_error(settings, mocker, caplog):
    """
    Tests that `fetch_emeritus_courses` specific calls to the Emeritus API and Fails for Job status 3 and 4.
    """
    settings.EMERITUS_API_BASE_URL = "https://test_emeritus_api.com"
    settings.EMERITUS_API_KEY = "test_emeritus_api_key"
    mock_get = mocker.patch(
        "courses.sync_external_courses.emeritus_api_client.requests.get"
    )
    mock_post = mocker.patch(
        "courses.sync_external_courses.emeritus_api_client.requests.post"
    )

    batch_query = {
        "id": 77,
        "name": "Batch",
    }
    mock_get.side_effect = [
        MockResponse({"results": [batch_query]}),
        MockResponse({"job": {"status": 1}}),
        MockResponse({"job": {"status": 2}}),
        MockResponse({"job": {"status": 4}}),
    ]
    mock_post.side_effect = [MockResponse({"job": {"id": 1}})]
    with caplog.at_level(logging.ERROR):
        fetch_emeritus_courses()
    assert "Job failed!" in caplog.text
    assert "Something unexpected happened!" in caplog.text
