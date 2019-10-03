"""
Admin site bindings for compliance
"""

from django.conf import settings
from django.contrib import admin

from mitxpro.utils import get_field_names
from users.utils import ensure_active_user

from .constants import RESULT_MANUALLY_APPROVED, RESULT_SUCCESS
from .models import ExportsInquiryLog


class ExportsInquiryLogAdmin(admin.ModelAdmin):
    """Admin for ExportsInquiryLog"""

    model = ExportsInquiryLog
    search_fields = ["user__email", "computed_result", "info_code", "reason_code"]
    list_filter = ["computed_result", "info_code", "reason_code"]
    list_display = ["user", "computed_result", "info_code", "reason_code"]
    readonly_fields = [] if settings.DEBUG else get_field_names(ExportsInquiryLog)
    actions = ["manually_approve_inquiry"]

    def manually_approve_inquiry(self, request, queryset):
        """Admin action to manually approve export compliance inquiry records"""
        eligible_objects = queryset.exclude(
            computed_result__in=[RESULT_MANUALLY_APPROVED, RESULT_SUCCESS]
        )
        eligible_objects.update(computed_result=RESULT_MANUALLY_APPROVED)
        for obj in eligible_objects:
            ensure_active_user(obj.user)

    manually_approve_inquiry.short_description = "Manually approve selected records"

    def has_add_permission(self, request):
        # We want to allow this while debugging
        return settings.DEBUG

    def has_delete_permission(self, request, obj=None):
        # We want to allow this while debugging
        return settings.DEBUG


admin.site.register(ExportsInquiryLog, ExportsInquiryLogAdmin)
