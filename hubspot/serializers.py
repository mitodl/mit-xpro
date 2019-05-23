""" Serializers for HubSpot"""
from rest_framework import serializers

from ecommerce import models
from ecommerce.api import get_product_version_price_with_discount, round_half_up
from ecommerce.models import CouponVersion, ProductVersion, CouponRedemption


class LineSerializer(serializers.ModelSerializer):
    """ Line Serializer for Hubspot """

    product = serializers.IntegerField(source="product_version.product.id")

    class Meta:
        fields = ("id", "product")
        model = models.Line


class OrderToDealSerializer(serializers.ModelSerializer):
    """ Order/Deal Serializer for Hubspot """

    name = serializers.SerializerMethodField()
    close_date = serializers.SerializerMethodField(allow_null=True)
    amount = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    coupon_code = serializers.SerializerMethodField(allow_null=True)
    company = serializers.SerializerMethodField(allow_null=True)
    lines = LineSerializer(many=True)
    b2b = serializers.SerializerMethodField()

    _coupon_version = None
    _product_version = None
    _redemption = None

    def _get_coupon_version(self, instance):
        """Return the order coupon version"""
        if self._coupon_version is None:
            self._coupon_version = CouponVersion.objects.filter(
                couponredemption__order=instance
            ).first()
        return self._coupon_version

    def _get_product_version(self, instance):
        """Return the order product version"""
        if self._product_version is None:
            self._product_version = ProductVersion.objects.filter(
                id__in=instance.lines.values_list("product_version", flat=True)
            ).first()
        return self._product_version

    def _get_redemption(self, instance):
        """Return the order coupon redemption"""
        if self._redemption is None:
            self._redemption = CouponRedemption.objects.filter(order=instance).first()
        return self._redemption

    def get_name(self, instance):
        """ Return the order/deal name """
        return f"XPRO-ORDER-{instance.id}"

    def get_close_date(self, instance):
        """ Return the updated_on date (as a timestamp in milliseconds) if fulfilled """
        if instance.status == models.Order.FULFILLED:
            return int(instance.updated_on.timestamp() * 1000)

    def get_amount(self, instance):
        """ Get the amount paid after discount """
        return get_product_version_price_with_discount(
            coupon_version=self._get_coupon_version(instance),
            product_version=self._get_product_version(instance),
        ).to_eng_string()

    def get_discount_amount(self, instance):
        """ Get the discount amount if any """

        coupon_version = self._get_coupon_version(instance)
        if not coupon_version:
            return "0.00"

        return round_half_up(
            coupon_version.payment_version.amount
            * self._get_product_version(instance).price
        ).to_eng_string()

    def get_company(self, instance):
        """ Get the company id if any """
        redemption = self._get_redemption(instance)
        if redemption:
            company = redemption.coupon_version.payment_version.company
            if company:
                return company.id

    def get_coupon_code(self, instance):
        """ Get the coupon code used for the order if any """
        redemption = self._get_redemption(instance)
        if redemption:
            return redemption.coupon_version.coupon.coupon_code

    def get_b2b(self, instance):
        """ Determine if this is a B2B order """
        redemption = self._get_redemption(instance)
        if redemption:
            company = redemption.coupon_version.payment_version.company
            transaction_id = (
                redemption.coupon_version.payment_version.payment_transaction
            )
            if company or transaction_id:
                return True
        return False

    class Meta:
        fields = (
            "id",
            "name",
            "amount",
            "discount_amount",
            "close_date",
            "coupon_code",
            "lines",
            "purchaser",
            "status",
            "company",
            "b2b",
        )
        model = models.Order


class ProductSerializer(serializers.ModelSerializer):
    """ Product Serializer for Hubspot """

    title = serializers.SerializerMethodField()
    product_type = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    def get_title(self, instance):
        """ Return the product title """
        return instance.content_type.get_object_for_this_type(
            pk=instance.object_id
        ).title

    def get_product_type(self, instance):
        """ Return the product type """
        return instance.content_type.model

    def get_price(self, instance):
        """Return the latest product version price"""
        product_version = instance.latest_version
        if product_version:
            return product_version.price.to_eng_string()
        return "0.00"

    class Meta:
        fields = "__all__"
        model = models.Product
