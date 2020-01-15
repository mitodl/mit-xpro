"""Utility functions for ecommerce"""
import logging
from urllib.parse import urljoin, urlencode

from django.conf import settings
from django.core import mail
from django.urls import reverse

from ecommerce.exceptions import ParseException

log = logging.getLogger(__name__)


def create_delete_rule(table_name):
    """Helper function to make SQL to create a rule to prevent deleting from the ecommerce table"""
    return f"CREATE RULE delete_protect AS ON DELETE TO ecommerce_{table_name} DO INSTEAD NOTHING"


def create_update_rule(table_name):
    """Helper function to make SQL to create a rule to prevent updating a row in the ecommerce table"""
    return f"CREATE RULE update_protect AS ON UPDATE TO ecommerce_{table_name} DO INSTEAD NOTHING"


def rollback_delete_rule(table_name):
    """Helper function to make SQL to create a rule to allow deleting from the ecommerce table"""
    return f"DROP RULE delete_protect ON ecommerce_{table_name}"


def rollback_update_rule(table_name):
    """Helper function to make SQL to create a rule to allow updating from the ecommerce table"""
    return f"DROP RULE update_protect ON ecommerce_{table_name}"


def get_order_id_by_reference_number(*, reference_number, prefix):
    """
    Parse a reference number received from CyberSource and return the order id.

    Args:
        reference_number (str):
            A string which contains the order id and the instance which generated it
        prefix (str):
            The prefix string which is attached to the reference number to distinguish from other
            reference numbers in other environments.

    Returns:
        int: An order id
    """
    prefix_with_dash = f"{prefix}-"
    if not reference_number.startswith(prefix_with_dash):
        log.error(
            "CyberSource prefix doesn't match: should start with %s but is %s",
            prefix_with_dash,
            reference_number,
        )
        raise ParseException(f"Reference number must start with {prefix_with_dash}")
    try:
        order_id = int(reference_number[len(prefix_with_dash) :])
    except ValueError:
        raise ParseException("Unable to parse order number")

    return order_id


def send_support_email(subject, message):
    """
    Send an email to support.

    Args:
        subject (str): The email subject.
        message (str): The email message.
    """
    try:
        with mail.get_connection(settings.NOTIFICATION_EMAIL_BACKEND) as connection:
            mail.send_mail(
                subject,
                message,
                settings.ADMIN_EMAIL,
                [settings.EMAIL_SUPPORT],
                connection=connection,
            )
    except:  # pylint: disable=bare-except
        log.exception("Exception sending email to admins")


def make_checkout_url(*, product=None, code=None):
    """
    Helper function to create a checkout URL with appropriate query parameters.

    Args:
        product (Product): A Product instance
        code (str): The coupon code

    Returns:
        str: The URL for the checkout page, including product and coupon code if available
    """
    base_checkout_url = urljoin(settings.SITE_BASE_URL, reverse("checkout-page"))
    if product is None and code is None:
        return base_checkout_url

    query_params = {}
    if product is not None:
        if product.content_type.model == "courserun":
            readable_id = product.content_object.courseware_id
        else:
            readable_id = product.content_object.readable_id
        query_params["product"] = readable_id
    if code is not None:
        query_params["code"] = code
    return f"{base_checkout_url}?{urlencode(query_params)}"
