"""Ecommerce mail API tests"""
import pytest

from courses.factories import CourseRunEnrollmentFactory
from ecommerce.factories import (
    CouponPaymentVersionFactory,
    CouponEligibilityFactory,
    ProductVersionFactory,
    CompanyFactory,
)
from ecommerce.mail_api import send_bulk_enroll_emails, send_course_run_enrollment_email
from mail.constants import EMAIL_BULK_ENROLL, EMAIL_COURSE_RUN_ENROLLMENT

lazy = pytest.lazy_fixture

pytestmark = pytest.mark.django_db


@pytest.fixture()
def company():
    """Company object fixture"""
    return CompanyFactory.create(name="MIT")


@pytest.mark.parametrize("test_company", [lazy("company"), None])
def test_send_bulk_enroll_emails(mocker, settings, test_company):
    """
    send_bulk_enroll_emails should build messages for each recipient and send them
    """
    patched_mail_api = mocker.patch("ecommerce.mail_api.api")

    settings.SITE_BASE_URL = "http://test.com/"
    email = "a@b.com"
    payment_version = CouponPaymentVersionFactory.create(company=test_company)
    product_version = ProductVersionFactory.create()
    product_coupon = CouponEligibilityFactory.create(
        coupon__payment=payment_version.payment, product=product_version.product
    )

    expected_qs = "product={}&code={}".format(
        product_version.product.id, product_coupon.coupon.coupon_code
    )
    expected_context = {
        "enrollable_title": product_coupon.product.content_object.title,
        "enrollment_url": "http://test.com/checkout/?{}".format(expected_qs),
        "company_name": test_company.name if test_company else None,
    }

    send_bulk_enroll_emails([email], [product_coupon])

    patched_mail_api.build_user_specific_messages.assert_called_once()
    assert (
        patched_mail_api.build_user_specific_messages.call_args[0][0]
        == EMAIL_BULK_ENROLL
    )
    assert list(patched_mail_api.build_user_specific_messages.call_args[0][1]) == [
        (email, expected_context)
    ]

    patched_mail_api.send_messages.assert_called_once_with(
        patched_mail_api.build_user_specific_messages.return_value
    )


def test_send_course_run_enrollment_email(mocker):
    """send_course_run_enrollment_email should send an email for the given enrollment"""
    patched_mail_api = mocker.patch("ecommerce.mail_api.api")
    enrollment = CourseRunEnrollmentFactory.create()

    send_course_run_enrollment_email(enrollment)

    patched_mail_api.context_for_user.assert_called_once_with(
        user=enrollment.user, extra_context={"enrollment": enrollment}
    )
    patched_mail_api.message_for_recipient.assert_called_once_with(
        enrollment.user.email,
        patched_mail_api.context_for_user.return_value,
        EMAIL_COURSE_RUN_ENROLLMENT,
    )
    patched_mail_api.send_message.assert_called_once_with(
        patched_mail_api.message_for_recipient.return_value
    )


def test_send_course_run_enrollment_email_error(mocker):
    """send_course_run_enrollment_email handle and log errors"""
    patched_mail_api = mocker.patch("ecommerce.mail_api.api")
    patched_log = mocker.patch("ecommerce.mail_api.log")
    patched_mail_api.send_message.side_effect = Exception("error")
    enrollment = CourseRunEnrollmentFactory.create()

    send_course_run_enrollment_email(enrollment)

    patched_log.exception.assert_called_once_with(
        "Error sending enrollment success email"
    )
