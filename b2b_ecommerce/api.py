"""Functions for b2b_ecommerce"""
from decimal import Decimal
import uuid

from django.conf import settings
from django.db import transaction

from ecommerce.api import create_coupons, ISO_8601_FORMAT, sign_cybersource_payload
from ecommerce.models import CouponPaymentVersion
from mitxpro.utils import now_in_utc


def complete_b2b_order(order):
    """
    Create the enrollment codes which were paid for and link them to the purchaser.

    Args:
        order (B2BOrder): A fulfilled order for enrollment codes
    """
    with transaction.atomic():
        product_id = order.product_version.product.id
        payment_version = create_coupons(
            name=f"CouponPayment for order #{order.id}",
            product_ids=[product_id],
            amount=Decimal("1"),
            num_coupon_codes=order.num_seats,
            coupon_type=CouponPaymentVersion.SINGLE_USE,
        )
        order.coupon_payment_version = payment_version
        order.save()


def _generate_b2b_cybersource_sa_payload(*, order, receipt_url, cancel_url):
    """
    Generates a payload dict to send to CyberSource for Secure Acceptance for a B2BOrder
    Args:
        order (B2BOrder): An order for purchasing enrollment codes
        receipt_url (str): The URL to be used by Cybersource to redirect the user after completion of the purchase
        cancel_url (str): The URL to be used by Cybersource to redirect the user after they click cancel
    Returns:
        dict: the payload to send to CyberSource via Secure Acceptance
    """
    # http://apps.cybersource.com/library/documentation/dev_guides/Secure_Acceptance_WM/Secure_Acceptance_WM.pdf
    # Section: API Fields

    # NOTE: be careful about max length here, many (all?) string fields have a max
    # length of 255. At the moment none of these fields should go over that, due to database
    # constraints or other reasons

    product_version = order.product_version
    content_object = product_version.product.content_object
    content_type = str(product_version.product.content_type)
    price = order.total_price

    return {
        "access_key": settings.CYBERSOURCE_ACCESS_KEY,
        "amount": str(price),
        "currency": "USD",
        "locale": "en-us",
        "item_0_code": "enrollment_code",
        "item_0_name": f"Enrollment codes for {product_version.description}"[:254],
        "item_0_quantity": order.num_seats,
        "item_0_sku": f"enrollment_code-{content_type}-{content_object.id}"[:254],
        "item_0_tax_amount": "0",
        "item_0_unit_price": str(price),
        "line_item_count": 1,
        "reference_number": order.reference_id,
        "profile_id": settings.CYBERSOURCE_PROFILE_ID,
        "signed_date_time": now_in_utc().strftime(ISO_8601_FORMAT),
        "override_custom_receipt_page": receipt_url,
        "override_custom_cancel_page": cancel_url,
        "transaction_type": "sale",
        "transaction_uuid": uuid.uuid4().hex,
        "unsigned_field_names": "",
    }


def generate_b2b_cybersource_sa_payload(*, order, receipt_url, cancel_url):
    """
    Generates a payload dict to send to CyberSource for Secure Acceptance for a B2BOrder
    Args:
        order (B2BOrder): An order for purchasing enrollment codes
        receipt_url (str): The URL to be used by Cybersource to redirect the user after completion of the purchase
        cancel_url (str): The URL to be used by Cybersource to redirect the user after they click cancel
    Returns:
        dict: the payload to send to CyberSource via Secure Acceptance
    """
    return sign_cybersource_payload(
        _generate_b2b_cybersource_sa_payload(
            order=order, receipt_url=receipt_url, cancel_url=cancel_url
        )
    )
