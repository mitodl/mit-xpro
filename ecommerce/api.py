"""
Functions for ecommerce
"""
from base64 import b64encode
import hashlib
import hmac
import logging
import uuid

from django.conf import settings
from django.db.models import Q
from django.db import transaction

from ecommerce.models import (
    CouponEligibility,
    CouponVersion,
    CouponRedemption,
    CouponSelection,
    Order,
)
from mitxpro.utils import now_in_utc

ISO_8601_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
log = logging.getLogger(__name__)

_REFERENCE_NUMBER_PREFIX = "MITXPRO-"


def generate_cybersource_sa_signature(payload):
    """
    Generate an HMAC SHA256 signature for the CyberSource Secure Acceptance payload
    Args:
        payload (dict): The payload to be sent to CyberSource
    Returns:
        str: The signature
    """
    # This is documented in certain CyberSource sample applications:
    # http://apps.cybersource.com/library/documentation/dev_guides/Secure_Acceptance_SOP/html/wwhelp/wwhimpl/js/html/wwhelp.htm#href=creating_profile.05.6.html
    keys = payload["signed_field_names"].split(",")
    message = ",".join(f"{key}={payload[key]}" for key in keys)

    digest = hmac.new(
        settings.CYBERSOURCE_SECURITY_KEY.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    return b64encode(digest).decode("utf-8")


def generate_cybersource_sa_payload(order):
    """
    Generates a payload dict to send to CyberSource for Secure Acceptance
    Args:
        order (Order): An order
    Returns:
        dict: the payload to send to CyberSource via Secure Acceptance
    """
    # http://apps.cybersource.com/library/documentation/dev_guides/Secure_Acceptance_WM/Secure_Acceptance_WM.pdf
    # Section: API Fields

    # NOTE: be careful about max length here, many (all?) string fields have a max
    # length of 255. At the moment none of these fields should go over that, due to database
    # constraints or other reasons

    line_items = {}
    total = 0
    for i, line in enumerate(order.lines.all()):
        product_version = line.product_version
        line_items[f"item_{i}_code"] = str(product_version.product.content_type)
        line_items[f"item_{i}_name"] = str(product_version.description)[:254]
        line_items[f"item_{i}_quantity"] = line.quantity
        line_items[f"item_{i}_sku"] = product_version.product.content_object.id
        line_items[f"item_{i}_tax_amount"] = "0"
        line_items[f"item_{i}_unit_price"] = str(product_version.price)

        total += product_version.price

    payload = {
        "access_key": settings.CYBERSOURCE_ACCESS_KEY,
        "amount": str(total),
        "consumer_id": order.purchaser.username,
        "currency": "USD",
        "locale": "en-us",
        **line_items,
        "line_item_count": order.lines.count(),
        "reference_number": make_reference_id(order),
        "profile_id": settings.CYBERSOURCE_PROFILE_ID,
        "signed_date_time": now_in_utc().strftime(ISO_8601_FORMAT),
        "transaction_type": "sale",
        "transaction_uuid": uuid.uuid4().hex,
        "unsigned_field_names": "",
    }

    field_names = sorted(list(payload.keys()) + ["signed_field_names"])
    payload["signed_field_names"] = ",".join(field_names)
    payload["signature"] = generate_cybersource_sa_signature(payload)

    return payload


def make_reference_id(order):
    """
    Make a reference id
    Args:
        order (Order):
            An order
    Returns:
        str:
            A reference number for use with CyberSource to keep track of orders
    """
    return (
        f"{_REFERENCE_NUMBER_PREFIX}{settings.CYBERSOURCE_REFERENCE_PREFIX}-{order.id}"
    )


def get_valid_coupon_versions(product, user, auto_only=False, code=None):
    """
    Given a list of coupon ids, determine which of them are valid based on invoice version dates and redemptions.

    Args:
        product (Product): product to filter CouponEligibility by
        user (User): User of coupons
        auto_only (bool): Whether or not to filter by automatic=True
        code (str): A coupon code to filter by

    Returns:
        list of CouponVersion: CouponVersion objects sorted by discount, highest first.
    """
    valid_coupons = []
    now = now_in_utc()

    with transaction.atomic():
        # Get the ids of the latest coupon versions
        product_coupon_query = CouponEligibility.objects.select_related(
            "coupon"
        ).filter(product=product, coupon__enabled=True)
        if code:
            product_coupon_query = product_coupon_query.filter(coupon__coupon_code=code)

        cv_latest = (
            CouponVersion.objects.select_related("coupon")
            .filter(coupon__in=product_coupon_query.values_list("coupon", flat=True))
            .order_by("coupon", "-created_on")
            .distinct("coupon")
            .values_list("pk")
        )

        # filter by expiration and activation dates
        query = (
            CouponVersion.objects.select_related("invoice_version")
            .filter(pk__in=cv_latest)
            .filter(
                Q(invoice_version__expiration_date__gte=now)
                | Q(invoice_version__expiration_date__isnull=True)
            )
            .filter(
                Q(invoice_version__activation_date__lte=now)
                | Q(invoice_version__activation_date__isnull=True)
            )
        )

        if auto_only:
            query = query.filter(invoice_version__automatic=True)

        # filter by redemption counts
        for coupon_version in query:
            redemptions_global = (
                CouponRedemption.objects.select_related("coupon_version", "order")
                .filter(coupon_version=coupon_version)
                .filter(order__status=Order.FULFILLED)
            )
            redemptions_user = redemptions_global.filter(order__purchaser=user)
            if (
                coupon_version.invoice_version.max_redemptions
                > redemptions_global.count()
                and coupon_version.invoice_version.max_redemptions_per_user
                > redemptions_user.count()
            ):
                valid_coupons.append(coupon_version)
        return sorted(
            valid_coupons, key=lambda x: x.invoice_version.amount, reverse=True
        )


def best_coupon_for_basket(basket, auto_only=False, code=None):
    """
    Get the best eligible coupon for the basket.
    Assumes that the basket only contains one item/product.

    Args:
        basket (Basket): the basket Object
        auto_only (bool): Only retrieve `automatic` Coupons
        code (str): A coupon code to filter by

    Returns:
        CouponVersion: the CouponVersion with the highest discount, or None
    """
    basket_item = basket.basketitems.first()
    if basket_item:
        return best_coupon_for_product(
            basket_item.product, basket.user, auto_only=auto_only, code=code
        )
    return None


def best_coupon_for_product(product, user, auto_only=False, code=None):
    """
    Get the best eligible coupon for a product and user.

    Args:
        product (Product): the Product Object
        user (User): The user buying the product
        auto_only (bool): Only retrieve `automatic` Coupons
        code (str): A coupon code to filter by

    Returns:
        CouponVersion: the CouponVersion with the highest product discount, or None
    """
    validated_versions = get_valid_coupon_versions(product, user, auto_only, code=code)
    if validated_versions:
        return validated_versions[0]
    return None


def get_product_price(product):
    """
    Retrieve the price for the latest version of a product

    Args:
        product (Product): A product object

    Returns:
        Decimal: the price of a product
    """
    return product.productversions.order_by("-created_on").first().price


def get_discount_price(coupon_version, product):
    """
    Determine the new discounted price for a product after the coupon discount is applied

    Args:
        coupon_version (CouponVersion): the CouponVersion object
        product: (Product): the Product object

    Returns:
        Decimal: the discounted price for the Product
    """
    return (1 - coupon_version.invoice_version.amount) * get_product_price(product)


def select_coupon(coupon_version, basket):
    """
    Apply a coupon to a basket by creating/updating the CouponSelection for that basket.
    Assumes there should be only one CouponSelection per basket.

    Args:
        coupon_version (CouponVersion): a CouponVersion object
        basket: (Basket): a Basket object

    Returns:
        CouponSelection: a coupon selection object

    """
    coupon_selection, _ = CouponSelection.objects.update_or_create(
        basket=basket, defaults={"coupon": coupon_version.coupon}
    )
    return coupon_selection


def redeem_coupon(coupon_version, order):
    """
    Redeem a coupon for an order by creating/updating the CouponRedemption for that order.
    Assumes there should only be one CouponRedemption per order.

    Args:
        coupon_version (CouponVersion): a CouponVersion object
        order: (Order): an Order object

    Returns:
        CouponRedemption: a CouponRedemption object

    """
    coupon_redemption, _ = CouponRedemption.objects.update_or_create(
        order=order, defaults={"coupon_version": coupon_version}
    )
    return coupon_redemption
