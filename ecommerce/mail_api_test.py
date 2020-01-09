"""Ecommerce mail API tests"""
from urllib.parse import urljoin

import datetime
from django.urls import reverse
import pytest
import factory
from pytz import UTC

from b2b_ecommerce.factories import B2BOrderFactory
from courses.factories import CourseRunEnrollmentFactory, CourseRunFactory
from ecommerce.api import get_readable_id
from ecommerce.factories import (
    CouponPaymentVersionFactory,
    BulkCouponAssignmentFactory,
    ProductCouponAssignmentFactory,
    CompanyFactory,
    LineFactory,
    ReceiptFactory,
)
from ecommerce.mail_api import (
    send_b2b_receipt_email,
    send_bulk_enroll_emails,
    send_course_run_enrollment_email,
    send_ecommerce_order_receipt,
)
from ecommerce.constants import BULK_ENROLLMENT_EMAIL_TAG
from ecommerce.models import Order
from mail.api import UserMessageProps, EmailMetadata
from mail.constants import (
    EMAIL_BULK_ENROLL,
    EMAIL_COURSE_RUN_ENROLLMENT,
    EMAIL_B2B_RECEIPT,
    EMAIL_PRODUCT_ORDER_RECEIPT,
)
from mitxpro.utils import format_price
from users.factories import UserFactory

lazy = pytest.lazy_fixture

pytestmark = pytest.mark.django_db


@pytest.fixture()
def company():
    """Company object fixture"""
    return CompanyFactory.create(name="MIT")


def test_send_bulk_enroll_emails(mocker, settings):
    """
    send_bulk_enroll_emails should build messages for each recipient and send them
    """
    patched_send_messages = mocker.patch("ecommerce.mail_api.api.send_messages")
    patched_build_user_messages = mocker.patch(
        "ecommerce.mail_api.api.build_user_specific_messages"
    )
    settings.SITE_BASE_URL = "http://test.com/"

    num_assignments = 2
    bulk_assignment = BulkCouponAssignmentFactory.create()
    assignments = ProductCouponAssignmentFactory.create_batch(
        num_assignments, bulk_assignment=bulk_assignment
    )
    new_company = CompanyFactory.create()
    new_coupon_payment_versions = CouponPaymentVersionFactory.create_batch(
        num_assignments,
        payment=factory.Iterator(
            [assignment.product_coupon.coupon.payment for assignment in assignments]
        ),
        company=factory.Iterator([new_company, None]),
    )

    send_bulk_enroll_emails(bulk_assignment.id, assignments)

    patched_send_messages.assert_called_once()
    patched_build_user_messages.assert_called_once()
    assert patched_build_user_messages.call_args[0][0] == EMAIL_BULK_ENROLL
    recipients_and_contexts_arg = list(patched_build_user_messages.call_args[0][1])
    for i, assignment in enumerate(assignments):
        product_type_str = assignment.product_coupon.product.type_string
        user_message_props = recipients_and_contexts_arg[i]
        assert isinstance(user_message_props, UserMessageProps) is True
        assert user_message_props.recipient == assignment.email
        assert user_message_props.context == {
            "enrollable_title": assignment.product_coupon.product.content_object.title,
            "enrollment_url": "http://test.com/checkout/?product={}&code={}".format(
                assignment.product_coupon.product.id,
                assignment.product_coupon.coupon.coupon_code,
            ),
            "company_name": (
                None
                if not new_coupon_payment_versions[i].company
                else new_coupon_payment_versions[i].company.name
            ),
        }
        assert user_message_props.metadata == EmailMetadata(
            tags=[BULK_ENROLLMENT_EMAIL_TAG],
            user_variables={
                "bulk_assignment": bulk_assignment.id,
                "enrollment_code": assignment.product_coupon.coupon.coupon_code,
                product_type_str: assignment.product_coupon.product.content_object.text_id,
            },
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


@pytest.mark.parametrize("has_discount", [True, False])
def test_send_b2b_receipt_email(mocker, settings, has_discount):
    """send_b2b_receipt_email should send a receipt email"""
    patched_mail_api = mocker.patch("ecommerce.mail_api.api")
    order = B2BOrderFactory.create()
    if has_discount:
        discount = order.total_price / 3
        order.discount = discount
        order.total_price -= discount
        order.save()

    send_b2b_receipt_email(order)

    format_string = "%b %-d, %Y"
    run = order.product_version.product.content_object
    download_url = f'{urljoin(settings.SITE_BASE_URL, reverse("bulk-enrollment-code-receipt"))}?hash={str(order.unique_id)}'

    patched_mail_api.context_for_user.assert_called_once_with(
        user=None,
        extra_context={
            "purchase_date": order.updated_on.strftime(format_string),
            "total_price": format_price(order.total_price),
            "item_price": format_price(order.per_item_price),
            "discount": format_price(order.discount) if has_discount else None,
            "num_seats": str(order.num_seats),
            "contract_number": order.contract_number,
            "readable_id": get_readable_id(run),
            "run_date_range": f"{run.start_date.strftime(format_string)} - {run.end_date.strftime(format_string)}",
            "title": run.title,
            "download_url": download_url,
            "email": order.email,
            "order_reference_id": order.reference_number,
        },
    )
    patched_mail_api.message_for_recipient.assert_called_once_with(
        order.email, patched_mail_api.context_for_user.return_value, EMAIL_B2B_RECEIPT
    )
    patched_mail_api.send_message.assert_called_once_with(
        patched_mail_api.message_for_recipient.return_value
    )


def test_send_b2b_receipt_email_error(mocker):
    """send_b2b_receipt_email should log an error and silence the exception if sending mail fails"""
    order = B2BOrderFactory.create()
    patched_mail_api = mocker.patch("ecommerce.mail_api.api")
    patched_log = mocker.patch("ecommerce.mail_api.log")
    patched_mail_api.send_message.side_effect = Exception("error")

    send_b2b_receipt_email(order)

    patched_log.exception.assert_called_once_with("Error sending receipt email")


@pytest.mark.parametrize(
    "receipt_data", [{"req_card_number": "1234", "req_card_type": "001"}]
)
def test_send_ecommerce_order_receipt(mocker, receipt_data):
    """send_ecommerce_order_receipt should send a receipt email"""
    patched_mail_api = mocker.patch("ecommerce.mail_api.api")
    date = datetime.datetime(2010, 1, 1, 0, tzinfo=UTC)
    user = UserFactory.create(
        name="test",
        email="test@example.com",
        legal_address__first_name="Test",
        legal_address__last_name="User",
        legal_address__street_address_1="11 Main Street",
        legal_address__country="US",
        legal_address__state_or_territory="US-CO",
        legal_address__city="Boulder",
        legal_address__postal_code="80309",
    )
    line = LineFactory.create(
        order__status=Order.CREATED,
        order__id=1,
        order__created_on=date,
        order__total_price_paid=0,
        order__purchaser=user,
        product_version__price=100,
        quantity=1,
        product_version__product__content_object=CourseRunFactory.create(
            title="test_run_title"
        ),
        product_version__product__content_object__course__readable_id="course:/v7/choose-agency",
    )
    # pylint: disable=expression-not-assigned
    (
        ReceiptFactory.create(order=line.order, data=receipt_data)
        if receipt_data
        else None
    )
    send_ecommerce_order_receipt(line.order)
    patched_mail_api.context_for_user.assert_called_once_with(
        user=None,
        extra_context={
            "coupon": None,
            "content_title": "test_run_title",
            "lines": [
                {
                    "quantity": 1,
                    "total_paid": "100.00",
                    "discount": "0.0",
                    "price": "100.00",
                    "readable_id": get_readable_id(
                        line.product_version.product.content_object
                    ),
                    "start_date": None,
                    "end_date": None,
                    "content_title": "test_run_title",
                }
            ],
            "order_total": 100.0,
            "order": {
                "id": 1,
                "created_on": line.order.created_on,
                "reference_number": "xpro-b2c-dev-1",
            },
            "receipt": {"card_number": "1234", "card_type": "Visa"},
            "purchaser": {
                "name": " ".join(["Test", "User"]),
                "email": "test@example.com",
                "street_address": ["11 Main Street"],
                "state_code": "CO",
                "postal_code": "80309",
                "city": "Boulder",
                "country": "United States",
            },
        },
    )
    patched_mail_api.messages_for_recipients.assert_called_once_with(
        [("test@example.com", patched_mail_api.context_for_user.return_value)],
        EMAIL_PRODUCT_ORDER_RECEIPT,
    )
