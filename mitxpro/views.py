"""
mitxpro views
"""
import json

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotFound, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.template.loader import render_to_string
from raven.contrib.django.raven_compat.models import client as sentry
from rest_framework.views import APIView
from rest_framework.response import Response

from mitxpro.serializers import AppContextSerializer
from mitxpro.templatetags.render_bundle import public_path


def get_js_settings_context(request):
    """
    Returns the template context key/value needed for templates that render
    JS settings as JSON.
    """
    js_settings = {
        "gaTrackingID": settings.GA_TRACKING_ID,
        "environment": settings.ENVIRONMENT,
        "public_path": public_path(request),
        "release_version": settings.VERSION,
        "recaptchaKey": settings.RECAPTCHA_SITE_KEY,
        "sentry_dsn": sentry.get_public_dsn(),
        "support_email": settings.EMAIL_SUPPORT,
        "site_name": settings.SITE_NAME,
    }
    return {"js_settings_json": json.dumps(js_settings)}


@csrf_exempt
def index(request, **kwargs):  # pylint: disable=unused-argument
    """
    The index view
    """
    return render(request, "index.html", context=get_js_settings_context(request))


def handler404(request, exception):
    """404: NOT FOUND ERROR handler"""
    response = render_to_string(
        "404.html", request=request, context=get_js_settings_context(request)
    )
    return HttpResponseNotFound(response)


def handler500(request):
    """500 INTERNAL SERVER ERROR handler"""
    response = render_to_string(
        "500.html", request=request, context=get_js_settings_context(request)
    )
    return HttpResponseServerError(response)


def restricted(request):
    """
    Views restricted to admins
    """
    if not (request.user and request.user.is_staff):
        raise PermissionDenied
    return render(request, "index.html", context=get_js_settings_context(request))


class AppContextView(APIView):
    """Renders the user context as JSON"""

    permission_classes = []

    def get(self, request, *args, **kwargs):
        """Read-only access"""
        return Response(AppContextSerializer(request).data)
