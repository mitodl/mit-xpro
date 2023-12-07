"""Tests for CMS views"""
from datetime import datetime, timedelta
from types import SimpleNamespace

import factory
import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from wagtail.core.models import Site

from cms.constants import (
    ALL_TOPICS,
    ON_DEMAND_WEBINAR,
    UPCOMING_WEBINAR,
    WEBINAR_DEFAULT_IMAGES,
)
from cms.factories import (
    BlogIndexPageFactory,
    CatalogPageFactory,
    CourseIndexPageFactory,
    CoursePageFactory,
    HomePageFactory,
    ProgramIndexPageFactory,
    ProgramPageFactory,
    SignatoryPageFactory,
    TextSectionFactory,
    UserTestimonialsPageFactory,
    WebinarIndexPageFactory,
    WebinarPageFactory,
)
from cms.models import CourseIndexPage, HomePage, ProgramIndexPage, TextVideoSection
from courses.factories import (
    CourseRunCertificateFactory,
    CourseRunFactory,
    CourseTopicFactory,
    ProgramCertificateFactory,
    ProgramFactory,
    ProgramRunFactory,
)
from ecommerce.factories import ProductVersionFactory
from mitxpro.utils import now_in_utc


pytestmark = pytest.mark.django_db
# pylint: disable=redefined-outer-name,unused-argument


@pytest.fixture()
def wagtail_basics():
    """Fixture for Wagtail objects that we expect to always exist"""
    site = Site.objects.get(is_default_site=True)
    root = site.root_page
    return SimpleNamespace(site=site, root=root)


def test_custom_wagtail_api(client, admin_user):
    """
    We have a hook that alters the sorting of pages in the default Wagtail admin API. This test asserts that
    the admin API does not return an error as a result of that change.
    """
    client.force_login(admin_user)
    resp = client.get("/cms/api/main/pages/?child_of=1&for_explorer=1")
    assert resp.status_code == status.HTTP_200_OK


def test_wagtail_items_ordering(client, admin_user):
    """
    Assert that the pages returned by wagtail admin are alphabetically sorted
    """
    client.force_login(admin_user)
    home_page = HomePageFactory.create(title="Home Page", subhead="<p>subhead</p>")
    # Create random pages
    testimonial_page = UserTestimonialsPageFactory.create(
        parent=home_page, title="Testimonials"
    )
    signatory_page = SignatoryPageFactory.create(parent=home_page, title="Signatories")
    course_index_page = CourseIndexPageFactory.create(parent=home_page, title="Courses")
    program_index_page = ProgramIndexPageFactory.create(
        parent=home_page, title="Programs"
    )
    catalog_page = CatalogPageFactory.create(parent=home_page, title="Catalog")

    resp = client.get(
        "/cms/api/main/pages/?child_of={}&for_explorer=1".format(home_page.id)
    )
    assert resp.status_code == status.HTTP_200_OK
    items = list(resp.data.items())[1][1]  # Pages in response
    response_page_titles = [item["title"] for item in items]
    assert response_page_titles == [
        catalog_page.title,
        course_index_page.title,
        program_index_page.title,
        signatory_page.title,
        testimonial_page.title,
    ]


def test_home_page_view(client, wagtail_basics):
    """
    Test that the home page shows the right HTML for the watch now button
    """
    page = HomePage(title="Home Page", subhead="<p>subhead</p>")
    wagtail_basics.root.add_child(instance=page)
    resp = client.get(page.get_url())
    content = resp.content.decode("utf-8")

    # without watch now button
    assert (
        '<a id="actionButton" class="btn btn-primary text-uppercase px-5 py-2 action-button" href="#">Watch Now</a>'
        not in content
    )

    cache.clear()

    # add video section
    about_page = TextVideoSection(
        content="<p>content</p>", video_url="http://test.com/abcd"
    )
    page.add_child(instance=about_page)
    resp = client.get(page.get_url())
    content = resp.content.decode("utf-8")

    # with watch now button
    assert (
        '<a id="actionButton" class="btn btn-primary text-uppercase px-5 py-2 action-button" href="#">Watch Now</a>'
        in content
    )
    assert "dropdown-menu" not in content

    assert reverse("user-dashboard") not in content
    assert reverse("checkout-page") not in content


def test_home_page_context_topics(client, wagtail_basics):
    """
    Test that parent course topics are included in homepage context.
    """
    page = HomePage(title="Home Page", subhead="<p>subhead</p>")
    wagtail_basics.root.add_child(instance=page)

    parent_topic = CourseTopicFactory.create()
    child_topic = CourseTopicFactory.create(parent=parent_topic)

    resp = client.get(page.get_url())
    context = resp.context_data
    assert parent_topic.name in context["topics"]
    assert child_topic.name not in context["topics"]


def test_home_page_context_topics_ordering(client, wagtail_basics):
    """
    Test that course topics on HomePage are ordered alphabetically.
    """
    page = HomePage(title="Home Page", subhead="<p>subhead</p>")
    wagtail_basics.root.add_child(instance=page)

    topic_name_list = ["Analog", "Computer", "Business", "Technology", "Engineering"]
    CourseTopicFactory.create_batch(5, name=factory.Iterator(topic_name_list))

    resp = client.get(page.get_url())
    context = resp.context_data
    assert sorted(topic_name_list) == context["topics"]


def test_courses_index_view(client, wagtail_basics):
    """
    Test that the courses index page shows a 404
    """
    page, created = CourseIndexPage.objects.get_or_create()

    if created:
        wagtail_basics.root.add_child(instance=page)

    resp = client.get(page.get_url())
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_programs_index_view(client, wagtail_basics):
    """
    Test that the programs index page shows a 404
    """
    page, created = ProgramIndexPage.objects.get_or_create()

    if created:
        wagtail_basics.root.add_child(instance=page)

    resp = client.get(page.get_url())
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_course_program_child_view(client, wagtail_basics):
    """
    Test that course/program child pages show a 404
    """
    child_page = TextSectionFactory.create(parent=wagtail_basics.root)
    child_page.save_revision().publish()
    resp = client.get(child_page.get_url())
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_course_certificate_invalid_view(user_client, user, wagtail_basics):
    """
    Test that certificate page returns a 404 if CertificatePage does not exist for that course
    """
    home = HomePageFactory.create(parent=wagtail_basics.root, slug="home")
    home.save_revision().publish()

    course_page = CoursePageFactory.create(parent=home, certificate_page=None)
    course_page.save_revision().publish()

    course_run_certificate = CourseRunCertificateFactory.create(
        user=user, course_run__course=course_page.course
    )

    resp = user_client.get(course_run_certificate.link)
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_course_certificate_view(user_client, user, wagtail_basics):
    """
    Test that certificate page show correctly
    """
    home = HomePageFactory.create(parent=wagtail_basics.root, slug="home")
    home.save_revision().publish()

    course_page = CoursePageFactory.create(parent=home)
    course_page.save_revision().publish()

    course_run = CourseRunFactory.create(course=course_page.course)

    course_run_certificate = CourseRunCertificateFactory.create(
        user=user, course_run=course_run
    )

    resp = user_client.get(course_run_certificate.link)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.context_data["page"] == course_page.certificate_page
    assert resp.context_data["page"].certificate == course_run_certificate


def test_course_certificate_view_revoked_state(user_client, user, wagtail_basics):
    """
    Test that certificate page return 404 for revoked certificate.
    """
    home = HomePageFactory.create(parent=wagtail_basics.root, slug="home")
    home.save_revision().publish()

    course_page = CoursePageFactory.create(parent=home)
    course_page.save_revision().publish()

    course_run = CourseRunFactory.create(course=course_page.course)

    course_run_certificate = CourseRunCertificateFactory.create(
        user=user, course_run=course_run, is_revoked=False
    )

    resp = user_client.get(course_run_certificate.link)
    assert resp.status_code == status.HTTP_200_OK

    course_run_certificate.is_revoked = True
    course_run_certificate.save()
    resp = user_client.get(course_run_certificate.link)
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_program_certificate_invalid_view(user_client, user, wagtail_basics):
    """
    Test that program certificate page returns a 404 if CertificatePage does not exist for that program
    """
    home = HomePageFactory.create(parent=wagtail_basics.root, slug="home")
    home.save_revision().publish()

    program_page = ProgramPageFactory.create(parent=home, certificate_page=None)
    program_page.save_revision().publish()

    program_certificate = ProgramCertificateFactory.create(
        user=user, program=program_page.program
    )

    resp = user_client.get(program_certificate.link)
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_program_certificate_view(user_client, user, wagtail_basics):
    """
    Test that certificate page show correctly
    """
    home = HomePageFactory.create(parent=wagtail_basics.root, slug="home")
    home.save_revision().publish()

    program_page = ProgramPageFactory.create(parent=home)
    program_page.save_revision().publish()

    program_certificate = ProgramCertificateFactory.create(
        user=user, program=program_page.program
    )

    resp = user_client.get(program_certificate.link)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.context_data["page"] == program_page.certificate_page
    assert resp.context_data["page"].certificate == program_certificate


def test_catalog_page_product(client, wagtail_basics):
    """
    Verify that the catalog page does not include cards for either product pages
    that are not live (unpublished) or pages that have a product with live=False
    """
    homepage = wagtail_basics.root
    catalog_page = CatalogPageFactory.create(parent=homepage)
    catalog_page.save_revision().publish()

    now = now_in_utc()
    start_date = now + timedelta(days=2)
    end_date = now + timedelta(days=10)

    active_program_1 = ProgramFactory.create()
    active_program_2 = ProgramFactory.create()

    # Live course page and course with a future course run. Should be included in upcoming context
    active_course_run = CourseRunFactory.create(
        course__program=active_program_1,
        course__live=True,
        start_date=start_date,
        end_date=end_date,
        live=True,
    )

    # The course isn't live however it has a valid and live run and page. This should be filtered out in the
    # upcoming template context
    CourseRunFactory.create(
        course__program=active_program_1,
        course__live=False,
        start_date=start_date,
        end_date=end_date,
        live=True,
    )

    # The course is live but it has no page. This should be filtered out in the upcoming template context
    CourseRunFactory.create(
        course__program=active_program_2,
        course__live=True,
        course__page=None,
        start_date=start_date,
        end_date=end_date,
        live=True,
    )

    # Both the course and course run are live, but there is no course page
    # The program is also not live. These should both be filtered
    # out in the upcoming template context
    CourseRunFactory.create(
        course__live=True,
        course__program__live=False,
        course__page=False,
        start_date=start_date,
        end_date=end_date,
        live=True,
    )

    resp = client.get(catalog_page.get_url())
    assert resp.status_code == status.HTTP_200_OK
    assert resp.context_data["course_pages"] == [active_course_run.course.page]
    assert resp.context_data["program_pages"] == [
        active_program_1.page,
        active_program_2.page,
    ]


@pytest.mark.parametrize(
    "topic_filter, expected_courses_count, expected_program_count, expected_selected_topic",
    [
        [None, 2, 2, ALL_TOPICS],
        ["Engineering", 1, 1, "Engineering"],
        ["RandomTopic", 0, 0, "RandomTopic"],
    ],
)
def test_catalog_page_topics(  # pylint: disable=too-many-arguments
    client,
    wagtail_basics,
    topic_filter,
    expected_courses_count,
    expected_program_count,
    expected_selected_topic,
):
    """
    Test that topic filters are working fine.
    """
    # pylint:disable=too-many-locals
    homepage = wagtail_basics.root
    catalog_page = CatalogPageFactory.create(parent=homepage)
    catalog_page.save_revision().publish()

    now = now_in_utc()
    start_date = now + timedelta(days=2)
    end_date = now + timedelta(days=10)

    programs = ProgramFactory.create_batch(2)
    runs = CourseRunFactory.create_batch(
        2,
        course__program=factory.Iterator(programs),
        course__live=True,
        start_date=start_date,
        end_date=end_date,
        live=True,
    )

    course_pages = [run.course.coursepage for run in runs]
    parent_topics = CourseTopicFactory.create_batch(
        2, name=factory.Iterator(["Engineering", "Business"])
    )
    child_topics = CourseTopicFactory.create_batch(
        2,
        name=factory.Iterator(["Systems Engineering", "Commerce"]),
        parent=factory.Iterator(parent_topics),
    )

    for idx, course_page in enumerate(course_pages):
        course_page.topics.set([parent_topics[idx].id, child_topics[idx].id])

    if topic_filter:
        resp = client.get(f"{catalog_page.get_url()}?topic={topic_filter}")
    else:
        resp = client.get(catalog_page.get_url())

    assert resp.status_code == status.HTTP_200_OK
    assert sorted(resp.context_data["topics"]) == sorted(
        [ALL_TOPICS] + [topic.name for topic in parent_topics]
    )
    assert resp.context_data["selected_topic"] == expected_selected_topic
    assert len(resp.context_data["course_pages"]) == expected_courses_count
    assert len(resp.context_data["program_pages"]) == expected_program_count


def test_catalog_page_topics_ordering(client, wagtail_basics):
    """
    Test that topics are ordered alphabetically on Catalog Page
    """
    homepage = wagtail_basics.root
    catalog_page = CatalogPageFactory.create(parent=homepage)
    catalog_page.save_revision().publish()

    topic_name_without_courses_list = ["Analog", "Computer", "Business"]
    topic_name_with_courses_list = ["Technology", "Engineering"]

    CourseTopicFactory.create_batch(
        3, name=factory.Iterator(topic_name_without_courses_list)
    )
    parent_topics_with_courses = CourseTopicFactory.create_batch(
        2, name=factory.Iterator(topic_name_with_courses_list)
    )
    CourseRunFactory.create(course__page__topics=parent_topics_with_courses)

    resp = client.get(catalog_page.get_url())
    assert resp.status_code == status.HTTP_200_OK
    assert resp.context_data["topics"] == sorted(
        [ALL_TOPICS, *topic_name_with_courses_list]
    )


def test_program_page_checkout_url_product(client, wagtail_basics):
    """
    The checkout URL in the program page context should include the product ID if a product exists
    for the given program
    """
    program_page = ProgramPageFactory.create()
    program_page.save_revision().publish()
    product_version = ProductVersionFactory.create(
        product__content_object=program_page.program
    )
    resp = client.get(program_page.get_url())
    checkout_url = resp.context["checkout_url"]
    assert f"product={product_version.product.id}" in checkout_url


def test_program_page_checkout_url_program_run(client, wagtail_basics):
    """
    The checkout URL in the program page context should include the program run text ID if a program run exists
    """
    program_page = ProgramPageFactory.create()
    program_page.save_revision().publish()
    program_run = ProgramRunFactory.create(
        program=program_page.program, start_date=(now_in_utc() - timedelta(days=1))
    )
    resp = client.get(program_page.get_url())
    checkout_url = resp.context["checkout_url"]
    assert checkout_url is None

    program_run.start_date = now_in_utc() + timedelta(days=1)
    program_run.save()
    # If multiple future program runs exist, the one with the earliest start date should be used
    ProgramRunFactory.create(
        program=program_page.program,
        start_date=(program_run.start_date + timedelta(days=1)),
    )
    resp = client.get(program_page.get_url())
    checkout_url = resp.context["checkout_url"]
    assert f"product={program_run.full_readable_id}" in checkout_url


def test_program_page_for_program_run(client):
    """
    Test that program page URL works with program run id
    """
    program_page = ProgramPageFactory.create()
    program_page.save_revision().publish()
    program_run = ProgramRunFactory.create(
        program=program_page.program,
        run_tag="R1",
        start_date=(now_in_utc() + timedelta(days=10)),
    )

    page_base_url = program_page.get_url().rstrip("/")
    good_url = "{}+{}/".format(page_base_url, program_run.run_tag)
    resp = client.get(good_url)
    assert resp.status_code == 200
    bad_url = "{}+R2/".format(page_base_url)
    resp = client.get(bad_url)
    assert resp.status_code == 404


def test_webinar_page_context(client, wagtail_basics):
    """
    Test that the WebinarIndexPage returns the desired context
    """
    homepage = wagtail_basics.root
    webinar_index_page = WebinarIndexPageFactory.create(parent=homepage)
    webinar_index_page.save_revision().publish()

    resp = client.get(webinar_index_page.get_url())
    context = resp.context_data

    assert "webinars" in context
    assert ON_DEMAND_WEBINAR not in context["webinars"]
    assert UPCOMING_WEBINAR not in context["webinars"]

    WebinarPageFactory.create_batch(3, parent=webinar_index_page)
    WebinarPageFactory.create_batch(
        2, category=ON_DEMAND_WEBINAR, date=None, parent=webinar_index_page
    )

    resp = client.get(webinar_index_page.get_url())
    context = resp.context_data

    assert "webinars" in context
    assert len(context["webinars"][ON_DEMAND_WEBINAR]) == 2
    assert len(context["webinars"][UPCOMING_WEBINAR]) == 3
    assert context["webinar_default_images"] == WEBINAR_DEFAULT_IMAGES


def test_webinar_formatted_date(wagtail_basics):
    """
    Test that `WebinarPage.formatted_date` returns date in specific format.
    """
    homepage = wagtail_basics.root
    webinar_index_page = WebinarIndexPageFactory.create(parent=homepage)
    webinar_index_page.save_revision().publish()

    start_date = datetime.strptime("Tuesday, May 2, 2023", "%A, %B %d, %Y")
    webinar = WebinarPageFactory.create(parent=webinar_index_page, date=start_date)

    assert webinar.formatted_date == "Tuesday, May 2, 2023"


def test_upcoming_webinar_datetime_validations(wagtail_basics):
    """
    Test that the webinar page raises ValidationError when Date and Time is not provided for the upcoming webinars.
    """
    homepage = wagtail_basics.root
    webinar_index_page = WebinarIndexPageFactory.create(parent=homepage)
    webinar_index_page.save_revision().publish()

    with pytest.raises(ValidationError, match="cannot be empty for Upcoming Webinars."):
        WebinarPageFactory.create(parent=webinar_index_page, date=None, time=None)


def test_blog_page_context(client, wagtail_basics):
    """
    Test that the BlogIndexPage returns the desired context
    """
    homepage = wagtail_basics.root
    blog_index_page = BlogIndexPageFactory.create(parent=homepage)
    blog_index_page.save_revision().publish()

    resp = client.get(blog_index_page.get_url())
    context = resp.context_data

    assert "posts" in context
