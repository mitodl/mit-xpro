"""HTTP views for sheets app"""
import logging
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from rest_framework import status

# NOTE: Due to an unresolved bug (https://github.com/PyCQA/pylint/issues/2108), the
# `google` package (and other packages without an __init__.py file) will break pylint.
# The `disable-all` rules are here until that bug is fixed.
from google_auth_oauthlib.flow import Flow  # pylint: disable-all
from google.auth.exceptions import GoogleAuthError  # pylint: disable-all

from sheets.models import GoogleApiAuth
from sheets.constants import REQUIRED_GOOGLE_API_SCOPES
from sheets.utils import generate_google_client_config
from sheets import tasks
from sheets.api import CouponRequestHandler, CouponAssignmentHandler

log = logging.getLogger(__name__)


@staff_member_required(login_url="login")
def sheets_admin_view(request):
    """Admin view that renders a page that allows a user to begin Google OAuth auth"""
    existing_api_auth = GoogleApiAuth.objects.first()
    successful_action = request.GET.get("success")
    return render(
        request,
        "admin.html",
        {
            "existing_api_auth": existing_api_auth,
            "auth_completed": successful_action == "auth",
            "alternative_sheets_processing": settings.FEATURES.get(
                "COUPON_SHEETS_ALT_PROCESSING", False
            ),
            "coupon_requests_processed": successful_action == "coupon-request",
            "coupon_assignments_processed": successful_action == "coupon-assignment",
            "coupon_message_statuses_updated": successful_action
            == "coupon-message-status",
        },
    )


@staff_member_required(login_url="login")
def request_google_auth(request):
    """Admin view to begin Google OAuth auth"""
    flow = Flow.from_client_config(
        generate_google_client_config(), scopes=REQUIRED_GOOGLE_API_SCOPES
    )
    flow.redirect_uri = urljoin(settings.SITE_BASE_URL, reverse("complete-google-auth"))
    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )
    request.session["state"] = state
    request.session["code_verifier"] = flow.code_verifier
    return redirect(authorization_url)


@csrf_exempt
def complete_google_auth(request):
    """Admin view that handles the redirect from Google after completing Google auth"""
    state = request.session.get("state")
    if not state:
        raise GoogleAuthError(
            "Could not complete Google auth - 'state' was not found in the session"
        )
    flow = Flow.from_client_config(
        generate_google_client_config(), scopes=REQUIRED_GOOGLE_API_SCOPES, state=state
    )
    flow.redirect_uri = urljoin(settings.SITE_BASE_URL, reverse("complete-google-auth"))
    flow.code_verifier = request.session["code_verifier"]
    flow.fetch_token(code=request.GET.get("code"))

    # Store credentials
    credentials = flow.credentials
    with transaction.atomic():
        google_api_auth, _ = GoogleApiAuth.objects.select_for_update().get_or_create()
        google_api_auth.requesting_user = request.user
        google_api_auth.access_token = credentials.token
        google_api_auth.refresh_token = credentials.refresh_token
        google_api_auth.save()

    return redirect("{}?success=auth".format(reverse("sheets-admin-view")))


@csrf_exempt
def handle_coupon_request_sheet_update(request):
    """View that handles requests sent from Google's push notification service when a file changes"""
    tasks.handle_unprocessed_coupon_requests.delay()
    return HttpResponse(status=status.HTTP_200_OK)


@require_http_methods(["POST"])
@staff_member_required(login_url="login")
def process_request_sheet(request):
    """Helper view to process the coupon request Sheet"""
    coupon_request_handler = CouponRequestHandler()
    processed_requests = coupon_request_handler.create_coupons_from_sheet()
    coupon_request_handler.write_results_to_sheets(processed_requests)
    return redirect("{}?success=coupon-request".format(reverse("sheets-admin-view")))


@require_http_methods(["POST"])
@staff_member_required(login_url="login")
def process_assignment_sheets(request):
    """Helper view to process coupon assignment Sheets"""
    coupon_assignment_handler = CouponAssignmentHandler()
    coupon_assignment_handler.process_assignment_spreadsheets()
    return redirect("{}?success=coupon-assignment".format(reverse("sheets-admin-view")))


@require_http_methods(["POST"])
@staff_member_required(login_url="login")
def update_assignment_delivery_statuses(request):
    """
    Helper view to update message delivery statuses for coupon assignments in assignment Sheets
    that have not yet been completed
    """
    coupon_assignment_handler = CouponAssignmentHandler()
    coupon_assignment_handler.update_incomplete_assignment_message_statuses()
    return redirect(
        "{}?success=coupon-message-status".format(reverse("sheets-admin-view"))
    )
