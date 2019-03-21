"""Courseware API functions"""
from datetime import timedelta
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from rest_framework import status

from django.conf import settings
from django.db import transaction
from django.shortcuts import reverse
from oauth2_provider.models import Application, AccessToken
from oauthlib.common import generate_token

from authentication import api as auth_api
from courseware.exceptions import OpenEdXOAuth2Error, CoursewareUserCreateError
from courseware.models import CoursewareUser, OpenEdxApiAuth
from courseware.constants import PLATFORM_EDX
from mitxpro.utils import now_in_utc


OPENEDX_REGISTER_USER_PATH = "/user_api/v1/account/registration/"
OPENEDX_REQUEST_DEFAULTS = dict(country="US", honor_code=True)

OPENEDX_SOCIAL_LOGIN_XPRO_PATH = "/auth/login/mitxpro-oauth2/?auth_entry=login"
OPENEDX_OAUTH2_AUTHORIZE_PATH = "/oauth2/authorize"
OPENEDX_OAUTH2_ACCESS_TOKEN_PATH = "/oauth2/access_token"
OPENEDX_OAUTH2_SCOPES = ["read", "write"]
OPENEDX_OAUTH2_ACCESS_TOKEN_PARAM = "code"
OPENEDX_OAUTH2_ACCESS_TOKEN_EXPIRY_MARGIN_SECONDS = 10


def edx_url(path):
    """Returns the full url to the provided path"""
    return urljoin(settings.OPENEDX_API_BASE_URL, path)


def create_edx_user(user):
    """Makes a request to create an equivalent user in Open edX"""
    application = Application.objects.get(name=settings.OPENEDX_OAUTH_APP_NAME)
    expiry_date = now_in_utc() + timedelta(hours=settings.OPENEDX_TOKEN_EXPIRES_HOURS)
    access_token, _ = AccessToken.objects.update_or_create(
        user=user,
        application=application,
        defaults=dict(token=generate_token(), expires=expiry_date),
    )

    with transaction.atomic():
        _, created = CoursewareUser.objects.select_for_update().get_or_create(
            user=user, platform=PLATFORM_EDX
        )

        if not created:
            return

        # a non-200 status here will ensure we rollback creation of the CoursewareUser and try again
        resp = requests.post(
            edx_url(OPENEDX_REGISTER_USER_PATH),
            data=dict(
                username=user.username,
                email=user.email,
                name=user.name,
                provider=settings.MITXPRO_OAUTH_PROVIDER,
                access_token=access_token.token,
                **OPENEDX_REQUEST_DEFAULTS,
            ),
        )
        # edX responds with 200 on success, not 201
        if resp.status_code != status.HTTP_200_OK:
            raise CoursewareUserCreateError(
                f"Error creating Open edX user, got status_code={resp.status_code}"
            )


@transaction.atomic
def create_edx_auth_token(user):
    """
    Creates refresh token for LMS for the user

    Args:
        user(User): the user to create the record for

    Returns:
        OpenEdXAuth: auth model with refresh_token populated
    """

    # In order to acquire auth tokens from Open edX we need to perform the following steps:
    #
    # 1. Create a persistent session so that state is retained like a browser
    # 2. Initialize a session cookie for xPro, this emulates a user login
    # 3. Initiate an Open edX login, delegates to xPro using the session cookie
    # 4. Initiate an Open edX OAuth2 authorization for xPro
    # 5. Redirects back to xPro with the access token
    # 6. Redeem access token for a refresh/access token pair

    # ensure only we can update this for the duration of the
    auth, _ = OpenEdxApiAuth.objects.select_for_update().get_or_create(user=user)

    # we locked on the previous operation and something else populated these values
    if auth.refresh_token and auth.access_token:
        return auth

    # Step 1
    with requests.Session() as req_session:
        # Step 2
        django_session = auth_api.create_user_session(user)
        session_cookie = requests.cookies.create_cookie(
            name=settings.SESSION_COOKIE_NAME,
            domain=urlparse(settings.SITE_BASE_URL).hostname,
            path=settings.SESSION_COOKIE_PATH,
            value=django_session.session_key,
        )
        req_session.cookies.set_cookie(session_cookie)

        # Step 3
        url = edx_url(OPENEDX_SOCIAL_LOGIN_XPRO_PATH)
        resp = req_session.get(url)
        resp.raise_for_status()

        # Step 4
        redirect_uri = urljoin(
            settings.SITE_BASE_URL, reverse("openedx-private-oauth-complete")
        )
        url = edx_url(OPENEDX_OAUTH2_AUTHORIZE_PATH)
        params = dict(
            client_id=settings.OPENEDX_API_CLIENT_ID,
            scope=" ".join(OPENEDX_OAUTH2_SCOPES),
            redirect_uri=redirect_uri,
            response_type="code",
        )
        resp = req_session.get(url, params=params)
        resp.raise_for_status()

        # Step 5
        if not resp.url.startswith(redirect_uri):
            raise OpenEdXOAuth2Error(
                f"Redirected to '{resp.url}', expected: '{redirect_uri}'"
            )
        qs = parse_qs(urlparse(resp.url).query)
        if not qs.get(OPENEDX_OAUTH2_ACCESS_TOKEN_PARAM):
            raise OpenEdXOAuth2Error("Did not receive access_token from Open edX")

        # Step 6
        auth = _create_tokens_and_update_auth(
            auth,
            dict(
                code=qs[OPENEDX_OAUTH2_ACCESS_TOKEN_PARAM],
                grant_type="authorization_code",
                client_id=settings.OPENEDX_API_CLIENT_ID,
                client_secret=settings.OPENEDX_API_CLIENT_SECRET,
                redirect_uri=redirect_uri,
            ),
        )

    return auth


def _create_tokens_and_update_auth(auth, params):
    """
    Updates an OpenEdxApiAuth given the passed params

    Args:
        auth (courseware.models.OpenEdxApiAuth): the api auth credentials to update with the given params
        params (dict): the params to pass to the access token endpoint

    Returns:
        courseware.models.OpenEdxApiAuth:
            the updated auth records
    """
    resp = requests.post(edx_url(OPENEDX_OAUTH2_ACCESS_TOKEN_PATH), data=params)
    resp.raise_for_status()

    result = resp.json()

    expires_in = (
        result["expires_in"] - OPENEDX_OAUTH2_ACCESS_TOKEN_EXPIRY_MARGIN_SECONDS
    )

    auth.refresh_token = result["refresh_token"]
    auth.access_token = result["access_token"]
    auth.access_token_expires_on = now_in_utc() + timedelta(seconds=expires_in)
    auth.save()
    return auth


@transaction.atomic
def refresh_edx_api_auth(user):
    """
    Updates the api tokens for the given user

    Args:
        user (users.models.User): the user to update auth for

    Returns:
        auth:
            updated OpenEdxApiAuth
    """

    auth = OpenEdxApiAuth.objects.select_for_update().get(user=user)

    # Note: this is subject to thundering herd problems, we should address this at some point
    return _create_tokens_and_update_auth(
        auth,
        dict(
            refresh_token=auth.refresh_token,
            grant_type="refresh_token",
            client_id=settings.OPENEDX_API_CLIENT_ID,
            client_secret=settings.OPENEDX_API_CLIENT_SECRET,
        ),
    )
