"""admin classes for ecommerce"""
from django.contrib import admin

from ecommerce.models import (
    Line,
    Order,
    OrderAudit,
    Receipt,
    Coupon,
    CouponVersion,
    CouponPaymentVersion,
    CouponPayment,
    CouponSelection,
    CouponEligibility,
    CouponRedemption,
    Product,
    ProductVersion,
    DataConsentAgreement,
    DataConsentUser,
    Company,
    ProductCouponAssignment,
)
import ecommerce.signals  # pylint:disable=unused-import

from hubspot.task_helpers import sync_hubspot_deal
from mitxpro.utils import get_field_names


class LineAdmin(admin.ModelAdmin):
    """Admin for Line"""

    model = Line

    readonly_fields = get_field_names(Line)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class OrderAdmin(admin.ModelAdmin):
    """Admin for Order"""

    model = Order
    list_filter = ("status",)
    list_display = ("id", "purchaser", "status", "created_on")
    search_fields = ("purchaser__username", "purchaser__email")

    readonly_fields = [name for name in get_field_names(Order) if name != "status"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        """
        Saves object and logs change to object
        """
        obj.save_and_log(request.user)
        sync_hubspot_deal(obj)


class OrderAuditAdmin(admin.ModelAdmin):
    """Admin for OrderAudit"""

    model = OrderAudit
    readonly_fields = get_field_names(OrderAudit)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReceiptAdmin(admin.ModelAdmin):
    """Admin for Receipt"""

    model = Receipt
    readonly_fields = get_field_names(Receipt)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CouponPaymentVersionInline(admin.StackedInline):
    """Admin Inline for CouponPaymentVersion objects"""

    model = CouponPaymentVersion
    readonly_fields = get_field_names(CouponPaymentVersion)
    extra = 0
    show_change_link = True
    can_delete = False
    ordering = ("-created_on",)
    min_num = 0


class CouponVersionInline(admin.StackedInline):
    """Admin Inline for CouponVersion objects"""

    model = CouponVersion
    readonly_fields = get_field_names(CouponVersion)
    extra = 0
    show_change_link = True
    can_delete = False
    ordering = ("-created_on",)
    min_num = 0


class CouponAdmin(admin.ModelAdmin):
    """Admin for Coupons"""

    model = Coupon
    save_on_top = True
    inlines = [CouponVersionInline]


class CouponPaymentAdmin(admin.ModelAdmin):
    """Admin for CouponPayments"""

    model = CouponPayment
    save_on_top = True
    inlines = [CouponPaymentVersionInline]


class CouponPaymentVersionAdmin(admin.ModelAdmin):
    """Admin for CouponPaymentVersions"""

    model = CouponPaymentVersion
    save_as = True
    save_as_continue = False
    save_on_top = True

    def has_delete_permission(self, request, obj=None):
        return False

    class Media:
        css = {"all": ("css/django-admin-version.css",)}


class CouponVersionAdmin(admin.ModelAdmin):
    """Admin for CouponVersions"""

    model = CouponVersion
    save_as = True
    save_as_continue = False
    save_on_top = True

    def has_delete_permission(self, request, obj=None):
        return False

    class Media:
        css = {"all": ("css/django-admin-version.css",)}


class CouponSelectionAdmin(admin.ModelAdmin):
    """Admin for CouponSelections"""

    model = CouponSelection


class CouponEligibilityAdmin(admin.ModelAdmin):
    """Admin for CouponEligibilitys"""

    model = CouponEligibility


class CouponRedemptionAdmin(admin.ModelAdmin):
    """Admin for CouponRedemptions"""

    model = CouponRedemption


class ProductVersionAdmin(admin.ModelAdmin):
    """Admin for ProductVersion"""

    model = ProductVersion
    save_as = True
    save_as_continue = False
    save_on_top = True

    def has_delete_permission(self, request, obj=None):
        return False

    class Media:
        css = {"all": ("css/django-admin-version.css",)}


class ProductVersionInline(admin.StackedInline):
    """Inline form for ProductVersion"""

    model = ProductVersion
    readonly_fields = get_field_names(ProductVersion)
    extra = 0
    show_change_link = True
    can_delete = False
    ordering = ("-created_on",)
    min_num = 0


class ProductAdmin(admin.ModelAdmin):
    """Admin for CouponRedemptions"""

    model = Product
    inlines = [ProductVersionInline]


class DataConsentUserAdmin(admin.ModelAdmin):
    """Admin for DataConsentUser"""

    list_display = ("id", "user", "created_on")
    search_fields = ("user__username", "user__email")

    model = DataConsentUser


class DataConsentUserInline(admin.StackedInline):
    """Admin Inline for DataConsentUser objects"""

    model = DataConsentUser
    extra = 1
    show_change_link = True


class DataConsentAgreementAdmin(admin.ModelAdmin):
    """Admin for DataConsentAgreement"""

    list_filter = ("company",)
    list_display = ("id", "company", "created_on")
    search_fields = ("company", "content")
    inlines = [DataConsentUserInline]

    model = DataConsentAgreement


class CompanyAdmin(admin.ModelAdmin):
    """Admin for Company"""

    model = Company


class ProductCouponAssignmentAdmin(admin.ModelAdmin):
    """Admin for ProductCouponAssignment"""

    model = ProductCouponAssignment


admin.site.register(Line, LineAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderAudit, OrderAuditAdmin)
admin.site.register(Receipt, ReceiptAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductVersion, ProductVersionAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(CouponVersion, CouponVersionAdmin)
admin.site.register(CouponPayment, CouponPaymentAdmin)
admin.site.register(CouponPaymentVersion, CouponPaymentVersionAdmin)
admin.site.register(CouponSelection, CouponSelectionAdmin)
admin.site.register(CouponEligibility, CouponEligibilityAdmin)
admin.site.register(CouponRedemption, CouponRedemptionAdmin)
admin.site.register(DataConsentAgreement, DataConsentAgreementAdmin)
admin.site.register(DataConsentUser, DataConsentUserAdmin)
admin.site.register(ProductCouponAssignment, ProductCouponAssignmentAdmin)
admin.site.register(Company, CompanyAdmin)
