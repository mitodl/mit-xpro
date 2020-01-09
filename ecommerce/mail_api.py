"""Ecommerce mail API"""
import logging
from urllib.parse import urlencode, urljoin

from django.conf import settings
from django.urls import reverse
import pycountry
from courses.models import CourseRun
from mail import api
from mail.constants import (
    EMAIL_B2B_RECEIPT,
    EMAIL_BULK_ENROLL,
    EMAIL_COURSE_RUN_ENROLLMENT,
    EMAIL_COURSE_RUN_UNENROLLMENT,
    EMAIL_PRODUCT_ORDER_RECEIPT,
)
from ecommerce.constants import BULK_ENROLLMENT_EMAIL_TAG
from ecommerce.utils import make_checkout_url
from mitxpro.utils import format_price

log = logging.getLogger()


def get_bulk_enroll_message_data(bulk_assignment_id, recipient, product_coupon):
    """
    Builds the tuple of data required for each recipient's bulk enrollment email

    Args:
        bulk_assignment_id (int): The id for the BulkCouponAssignment that this assignment belongs to
        recipient (str): The recipient email address
        product_coupon (CouponEligibility): The product coupon that was assigned to the given recipient

    Returns:
        ecommerce.api.UserMessageProps: An object containing user-specific message data
    """
    enrollment_url = make_checkout_url(
        product_id=product_coupon.product.id, code=product_coupon.coupon.coupon_code
    )
    company_name = (
        product_coupon.coupon.payment.versions.values_list("company__name", flat=True)
        .order_by("-created_on")
        .first()
    )
    product_object = product_coupon.product.content_object
    context = {
        "enrollable_title": product_object.title,
        "enrollment_url": enrollment_url,
        "company_name": company_name,
    }
    return api.UserMessageProps(
        recipient=recipient,
        context=context,
        metadata=api.EmailMetadata(
            tags=[BULK_ENROLLMENT_EMAIL_TAG],
            user_variables={
                "bulk_assignment": bulk_assignment_id,
                "enrollment_code": product_coupon.coupon.coupon_code,
                product_coupon.product.type_string: product_object.text_id,
            },
        ),
    )


def send_bulk_enroll_emails(bulk_assignment_id, product_coupon_assignments):
    """
    Sends an email for recipients to enroll in a courseware offering via coupon

    Args:
        bulk_assignment_id (int): The id for the BulkCouponAssignment that the assignments belong to
        product_coupon_assignments (iterable of ProductCouponAssignments):
            Product coupon assignments about which we want to notify the recipients
    """
    api.send_messages(
        api.build_user_specific_messages(
            EMAIL_BULK_ENROLL,
            (
                get_bulk_enroll_message_data(
                    bulk_assignment_id,
                    product_coupon_assignment.email,
                    product_coupon_assignment.product_coupon,
                )
                for product_coupon_assignment in product_coupon_assignments
            ),
        )
    )


def send_course_run_enrollment_email(enrollment):
    """
    Notify the user of successful enrollment for a course run

    Args:
        enrollment (CourseRunEnrollment): the enrollment for which to send the email
    """
    try:
        user = enrollment.user
        api.send_message(
            api.message_for_recipient(
                user.email,
                api.context_for_user(
                    user=user, extra_context={"enrollment": enrollment}
                ),
                EMAIL_COURSE_RUN_ENROLLMENT,
            )
        )
    except:  # pylint: disable=bare-except
        log.exception("Error sending enrollment success email")


def send_course_run_unenrollment_email(enrollment):
    """
    Notify the user of successful unenrollment for a course run

    Args:
        enrollment (CourseRunEnrollment): the enrollment for which to send the email
    """
    try:
        user = enrollment.user
        api.send_message(
            api.message_for_recipient(
                user.email,
                api.context_for_user(
                    user=user, extra_context={"enrollment": enrollment}
                ),
                EMAIL_COURSE_RUN_UNENROLLMENT,
            )
        )
    except Exception as exp:  # pylint: disable=broad-except
        log.exception("Error sending unenrollment success email: %s", exp)


def send_b2b_receipt_email(order):
    """
    Send an email summarizing the enrollment codes purchased by a user

    Args:
        order (b2b_ecommerce.models.B2BOrder):
            An order
    """
    from ecommerce.api import get_readable_id

    format_string = "%b %-d, %Y"

    course_run_or_program = order.product_version.product.content_object
    title = course_run_or_program.title

    if (
        isinstance(course_run_or_program, CourseRun)
        and course_run_or_program.start_date is not None
        and course_run_or_program.end_date is not None
    ):
        run = course_run_or_program
        date_range = f"{run.start_date.strftime(format_string)} - {run.end_date.strftime(format_string)}"
    else:
        date_range = ""

    download_url = (
        f'{urljoin(settings.SITE_BASE_URL, reverse("bulk-enrollment-code-receipt"))}?'
        f'{urlencode({"hash": str(order.unique_id)})}'
    )
    try:
        api.send_message(
            api.message_for_recipient(
                order.email,
                api.context_for_user(
                    user=None,
                    extra_context={
                        "purchase_date": order.updated_on.strftime(format_string),
                        "total_price": format_price(order.total_price),
                        "item_price": format_price(order.per_item_price),
                        "discount": format_price(order.discount)
                        if order.discount is not None
                        else None,
                        "contract_number": order.contract_number,
                        "num_seats": str(order.num_seats),
                        "readable_id": get_readable_id(
                            order.product_version.product.content_object
                        ),
                        "run_date_range": date_range,
                        "title": title,
                        "download_url": download_url,
                        "email": order.email,
                        "order_reference_id": order.reference_number,
                    },
                ),
                EMAIL_B2B_RECEIPT,
            )
        )
    except:  # pylint: disable=bare-except
        log.exception("Error sending receipt email")


def send_ecommerce_order_receipt(order, cyber_source_provided_email=None):
    """
    Send emails receipt summarizing the user purchase detail.

    Args:
        cyber_source_provided_email: Include the email address if user provide though CyberSource payment process.
        order: An order.
    """
    from ecommerce.serializers import OrderReceiptSerializer

    data = OrderReceiptSerializer(instance=order).data
    purchaser = data.get("purchaser")
    coupon = data.get("coupon")
    lines = data.get("lines")
    order = data.get("order")
    receipt = data.get("receipt")
    country = pycountry.countries.get(alpha_2=purchaser.get("country"))
    recipients = [purchaser.get("email")]
    if cyber_source_provided_email and cyber_source_provided_email not in recipients:
        recipients.append(cyber_source_provided_email)

    try:
        messages = list(
            api.messages_for_recipients(
                [
                    (
                        recipient,
                        api.context_for_user(
                            user=None,
                            extra_context={
                                "coupon": coupon,
                                "content_title": lines[0].get("content_title")
                                if lines
                                else None,
                                "lines": lines,
                                "order_total": sum(
                                    float(line["total_paid"]) for line in lines
                                ),
                                "order": order,
                                "receipt": receipt,
                                "purchaser": {
                                    "name": " ".join(
                                        [
                                            purchaser.get("first_name"),
                                            purchaser.get("last_name"),
                                        ]
                                    ),
                                    "email": purchaser.get("email"),
                                    "street_address": purchaser.get("street_address"),
                                    "state_code": purchaser.get(
                                        "state_or_territory"
                                    ).split("-")[-1],
                                    "postal_code": purchaser.get("postal_code"),
                                    "city": purchaser.get("city"),
                                    "country": country.name if country else None,
                                },
                            },
                        ),
                    )
                    for recipient in recipients
                ],
                EMAIL_PRODUCT_ORDER_RECEIPT,
            )
        )
        api.send_messages(messages)

    except:  # pylint: disable=bare-except
        log.exception("Error sending order receipt email.")
