"""Courseware API tests"""
# pylint: disable=redefined-outer-name
import operator as op
from datetime import timedelta
from urllib.parse import parse_qsl

import pytest
from oauth2_provider.models import Application, AccessToken
from oauthlib.common import generate_token
from freezegun import freeze_time
import responses
from requests.exceptions import HTTPError
from rest_framework import status

from courses.factories import CourseRunFactory, CourseRunEnrollmentFactory
from courseware.api import (
    create_user,
    create_edx_user,
    create_edx_auth_token,
    get_valid_edx_api_auth,
    get_edx_api_client,
    enroll_in_edx_course_runs,
    retry_failed_edx_enrollments,
    OPENEDX_AUTH_DEFAULT_TTL_IN_SECONDS,
    ACCESS_TOKEN_HEADER_NAME,
)
from courseware.constants import (
    PLATFORM_EDX,
    EDX_ENROLLMENT_PRO_MODE,
    EDX_ENROLLMENT_AUDIT_MODE,
    PRO_ENROLL_MODE_ERROR_TEXTS,
    COURSEWARE_REPAIR_GRACE_PERIOD_MINS,
)
from courseware.exceptions import (
    CoursewareUserCreateError,
    EdxApiEnrollErrorException,
    UnknownEdxApiEnrollException,
)
from courseware.factories import OpenEdxApiAuthFactory
from courseware.models import CoursewareUser, OpenEdxApiAuth
from mitxpro.utils import now_in_utc
from mitxpro.test_utils import MockResponse

pytestmark = [pytest.mark.django_db]


@pytest.fixture()
def application(settings):
    """Test data and settings needed for create_edx_user tests"""
    settings.OPENEDX_OAUTH_APP_NAME = "test_app_name"
    settings.OPENEDX_API_BASE_URL = "http://example.com"
    settings.MITXPRO_OAUTH_PROVIDER = "test_provider"
    settings.MITXPRO_REGISTRATION_ACCESS_TOKEN = "access_token"
    return Application.objects.create(
        name=settings.OPENEDX_OAUTH_APP_NAME,
        user=None,
        client_type="confidential",
        authorization_grant_type="authorization-code",
        skip_authorization=True,
    )


def test_create_user(user, mocker):
    """Test that create_user calls the correct APIs"""
    mock_create_edx_user = mocker.patch("courseware.api.create_edx_user")
    mock_create_edx_auth_token = mocker.patch("courseware.api.create_edx_auth_token")
    create_user(user)
    mock_create_edx_user.assert_called_with(user)
    mock_create_edx_auth_token.assert_called_with(user)


@responses.activate
@pytest.mark.parametrize("access_token_count", [0, 1, 3])
def test_create_edx_user(user, settings, application, access_token_count):
    """Test that create_edx_user makes a request to create an edX user"""
    responses.add(
        responses.POST,
        f"{settings.OPENEDX_API_BASE_URL}/user_api/v1/account/registration/",
        json=dict(success=True),
        status=status.HTTP_200_OK,
    )

    for _ in range(access_token_count):
        AccessToken.objects.create(
            user=user,
            application=application,
            token=generate_token(),
            expires=now_in_utc() + timedelta(hours=1),
        )

    create_edx_user(user)

    # An AccessToken should be created during execution
    created_access_token = AccessToken.objects.filter(application=application).last()
    assert (
        responses.calls[0].request.headers[ACCESS_TOKEN_HEADER_NAME]
        == settings.MITXPRO_REGISTRATION_ACCESS_TOKEN
    )
    assert dict(parse_qsl(responses.calls[0].request.body)) == {
        "username": user.username,
        "email": user.email,
        "name": user.name,
        "provider": settings.MITXPRO_OAUTH_PROVIDER,
        "access_token": created_access_token.token,
        "country": "US",
        "honor_code": "True",
    }
    assert (
        CoursewareUser.objects.filter(
            user=user, platform=PLATFORM_EDX, has_been_synced=True
        ).exists()
        is True
    )


@responses.activate
@pytest.mark.usefixtures("application")
def test_create_edx_user_conflict(settings, user):
    """Test that create_edx_user handles a 409 response from the edX API"""
    responses.add(
        responses.POST,
        f"{settings.OPENEDX_API_BASE_URL}/user_api/v1/account/registration/",
        json=dict(username="exists"),
        status=status.HTTP_409_CONFLICT,
    )

    with pytest.raises(CoursewareUserCreateError):
        create_edx_user(user)

    assert CoursewareUser.objects.count() == 0


@responses.activate
@freeze_time("2019-03-24 11:50:36")
def test_create_edx_auth_token(settings, user):
    """Tests create_edx_auth_token makes the expected incantations to create a OpenEdxApiAuth"""
    refresh_token = "abc123"
    access_token = "def456"
    code = "ghi789"
    responses.add(
        responses.GET,
        f"{settings.OPENEDX_API_BASE_URL}/auth/login/mitxpro-oauth2/?auth_entry=login",
        status=status.HTTP_200_OK,
    )
    responses.add(
        responses.GET,
        f"{settings.OPENEDX_API_BASE_URL}/oauth2/authorize",
        headers={
            "Location": f"{settings.SITE_BASE_URL}/login/_private/complete?code={code}"
        },
        status=status.HTTP_302_FOUND,
    )
    responses.add(
        responses.GET,
        f"{settings.SITE_BASE_URL}/login/_private/complete",
        status=status.HTTP_200_OK,
    )
    responses.add(
        responses.POST,
        f"{settings.OPENEDX_API_BASE_URL}/oauth2/access_token",
        json=dict(
            refresh_token=refresh_token, access_token=access_token, expires_in=3600
        ),
        status=status.HTTP_200_OK,
    )

    create_edx_auth_token(user)

    assert len(responses.calls) == 4
    assert dict(parse_qsl(responses.calls[3].request.body)) == dict(
        code=code,
        grant_type="authorization_code",
        client_id=settings.OPENEDX_API_CLIENT_ID,
        client_secret=settings.OPENEDX_API_CLIENT_SECRET,
        redirect_uri=f"{settings.SITE_BASE_URL}/login/_private/complete",
    )

    assert OpenEdxApiAuth.objects.filter(user=user).exists()

    auth = OpenEdxApiAuth.objects.get(user=user)

    assert auth.refresh_token == refresh_token
    assert auth.access_token == access_token
    # plus expires_in, minutes 10 seconds
    assert auth.access_token_expires_on == now_in_utc() + timedelta(
        minutes=59, seconds=50
    )


@responses.activate
@freeze_time("2019-03-24 11:50:36")
def test_get_valid_edx_api_auth_unexpired():
    """Tests get_valid_edx_api_auth returns the current record if it is valid long enough"""
    auth = OpenEdxApiAuthFactory.create()

    updated_auth = get_valid_edx_api_auth(auth.user)

    assert updated_auth is not None
    assert updated_auth.refresh_token == auth.refresh_token
    assert updated_auth.access_token == auth.access_token
    assert updated_auth.access_token_expires_on == auth.access_token_expires_on


@responses.activate
@freeze_time("2019-03-24 11:50:36")
def test_get_valid_edx_api_auth_expired(settings):
    """Tests get_valid_edx_api_auth fetches and updates the auth credentials if expired"""
    auth = OpenEdxApiAuthFactory.create(expired=True)
    refresh_token = "abc123"
    access_token = "def456"

    responses.add(
        responses.POST,
        f"{settings.OPENEDX_API_BASE_URL}/oauth2/access_token",
        json=dict(
            refresh_token=refresh_token, access_token=access_token, expires_in=3600
        ),
        status=status.HTTP_200_OK,
    )

    updated_auth = get_valid_edx_api_auth(auth.user)

    assert updated_auth is not None
    assert len(responses.calls) == 1
    assert dict(parse_qsl(responses.calls[0].request.body)) == dict(
        refresh_token=auth.refresh_token,
        grant_type="refresh_token",
        client_id=settings.OPENEDX_API_CLIENT_ID,
        client_secret=settings.OPENEDX_API_CLIENT_SECRET,
    )

    assert updated_auth.refresh_token == refresh_token
    assert updated_auth.access_token == access_token
    # plus expires_in, minutes 10 seconds
    assert updated_auth.access_token_expires_on == now_in_utc() + timedelta(
        minutes=59, seconds=50
    )


def test_get_edx_api_client(mocker, settings, user):
    """Tests that get_edx_api_client returns an EdxApi client"""
    settings.OPENEDX_API_BASE_URL = "http://example.com"
    auth = OpenEdxApiAuthFactory.build(user=user)
    mock_refresh = mocker.patch(
        "courseware.api.get_valid_edx_api_auth", return_value=auth
    )
    client = get_edx_api_client(user)
    assert client.credentials["access_token"] == auth.access_token
    assert client.base_url == settings.OPENEDX_API_BASE_URL
    mock_refresh.assert_called_with(
        user, ttl_in_seconds=OPENEDX_AUTH_DEFAULT_TTL_IN_SECONDS
    )


def test_enroll_in_edx_course_runs(mocker, user):
    """Tests that enroll_in_edx_course_runs uses the EdxApi client to enroll in course runs"""
    mock_client = mocker.MagicMock()
    enroll_return_values = ["result1", "result2"]
    mock_client.enrollments.create_student_enrollment = mocker.Mock(
        side_effect=enroll_return_values
    )
    mocker.patch("courseware.api.get_edx_api_client", return_value=mock_client)
    course_runs = CourseRunFactory.build_batch(2)
    enroll_results = enroll_in_edx_course_runs(user, course_runs)
    mock_client.enrollments.create_student_enrollment.assert_any_call(
        course_runs[0].courseware_id, mode=EDX_ENROLLMENT_PRO_MODE
    )
    mock_client.enrollments.create_student_enrollment.assert_any_call(
        course_runs[1].courseware_id, mode=EDX_ENROLLMENT_PRO_MODE
    )
    assert enroll_results == enroll_return_values


@pytest.mark.parametrize("error_text", PRO_ENROLL_MODE_ERROR_TEXTS)
def test_enroll_in_edx_course_runs_audit(mocker, user, error_text):
    """Tests that enroll_in_edx_course_runs fails over to attempting enrollment with 'audit' mode"""
    mock_client = mocker.MagicMock()
    pro_enrollment_response = MockResponse({"message": error_text})
    audit_result = {"good": "result"}
    mock_client.enrollments.create_student_enrollment = mocker.Mock(
        side_effect=[HTTPError(response=pro_enrollment_response), audit_result]
    )
    patched_log_error = mocker.patch("courseware.api.log.error")
    mocker.patch("courseware.api.get_edx_api_client", return_value=mock_client)

    course_run = CourseRunFactory.build()
    results = enroll_in_edx_course_runs(user, [course_run])
    assert mock_client.enrollments.create_student_enrollment.call_count == 2
    mock_client.enrollments.create_student_enrollment.assert_any_call(
        course_run.courseware_id, mode=EDX_ENROLLMENT_PRO_MODE
    )
    mock_client.enrollments.create_student_enrollment.assert_any_call(
        course_run.courseware_id, mode=EDX_ENROLLMENT_AUDIT_MODE
    )
    assert results == [audit_result]
    patched_log_error.assert_called_once()


def test_enroll_pro_api_fail(mocker, user):
    """
    Tests that enroll_in_edx_course_runs raises an EdxApiEnrollErrorException if the request fails
    for some reason besides an enrollment mode error
    """
    mock_client = mocker.MagicMock()
    pro_enrollment_response = MockResponse({"message": "no dice"}, status_code=401)
    mock_client.enrollments.create_student_enrollment = mocker.Mock(
        side_effect=HTTPError(response=pro_enrollment_response)
    )
    mocker.patch("courseware.api.get_edx_api_client", return_value=mock_client)
    course_run = CourseRunFactory.build()

    with pytest.raises(EdxApiEnrollErrorException):
        enroll_in_edx_course_runs(user, [course_run])


def test_enroll_pro_unknown_fail(mocker, user):
    """
    Tests that enroll_in_edx_course_runs raises an UnknownEdxApiEnrollException if an unexpected exception
    is encountered
    """
    mock_client = mocker.MagicMock()
    mock_client.enrollments.create_student_enrollment = mocker.Mock(
        side_effect=ValueError("Unexpected error")
    )
    mocker.patch("courseware.api.get_edx_api_client", return_value=mock_client)
    course_run = CourseRunFactory.build()

    with pytest.raises(UnknownEdxApiEnrollException):
        enroll_in_edx_course_runs(user, [course_run])


@pytest.mark.parametrize("exception_raised", [Exception("An error happened"), None])
def test_retry_failed_edx_enrollments(mocker, exception_raised):
    """
    Tests that retry_failed_edx_enrollments loops through enrollments that failed in edX
    and attempts to enroll them again
    """
    with freeze_time(now_in_utc() - timedelta(days=1)):
        failed_enrollments = CourseRunEnrollmentFactory.create_batch(
            3, edx_enrolled=False
        )
    patched_enroll_in_edx = mocker.patch(
        "courseware.api.enroll_in_edx_course_runs",
        side_effect=[None, exception_raised or None, None],
    )
    patched_log_exception = mocker.patch("courseware.api.log.exception")
    expected_successful_enrollments = (
        failed_enrollments
        if not exception_raised
        else op.itemgetter(0, 2)(failed_enrollments)
    )
    successful_enrollments = retry_failed_edx_enrollments()

    assert patched_enroll_in_edx.call_count == len(failed_enrollments)
    assert set(e.id for e in successful_enrollments) == set(
        e.id for e in expected_successful_enrollments
    )
    assert patched_log_exception.called == (exception_raised is not None)


def test_retry_failed_enroll_grace_period(mocker):
    """
    Tests that retry_failed_edx_enrollments does not attempt to repair any enrollments that were recently created
    """
    now = now_in_utc()
    with freeze_time(now - timedelta(minutes=COURSEWARE_REPAIR_GRACE_PERIOD_MINS - 1)):
        CourseRunEnrollmentFactory.create(edx_enrolled=False)
    with freeze_time(now - timedelta(minutes=COURSEWARE_REPAIR_GRACE_PERIOD_MINS + 1)):
        older_enrollment = CourseRunEnrollmentFactory.create(edx_enrolled=False)
    patched_enroll_in_edx = mocker.patch("courseware.api.enroll_in_edx_course_runs")
    successful_enrollments = retry_failed_edx_enrollments()

    assert successful_enrollments == [older_enrollment]
    patched_enroll_in_edx.assert_called_once_with(
        older_enrollment.user, [older_enrollment.run]
    )
