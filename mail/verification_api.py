"""API for email verifications"""
from urllib.parse import quote_plus

from django.urls import reverse

from mail import api
from mail.constants import EMAIL_VERIFICATION


def send_verification_email(
    strategy, backend, code, partial_token
):  # pylint: disable=unused-argument
    """
    Sends a verification email for python-social-auth

    Args:
        strategy (social_django.strategy.DjangoStrategy): the strategy used to authenticate
        backend (social_core.backends.base.BaseAuth): the backend being used to authenticate
        code (social_django.models.Code): the confirmation code used to confirm the email address
        partial_token (str): token used to resume a halted pipeline
    """
    url = "{}?verification_code={}&partial_token={}".format(
        strategy.build_absolute_uri(reverse("register-confirm")),
        quote_plus(code.code),
        quote_plus(partial_token),
    )

    api.send_message(
        api.message_for_recipient(
            code.email,
            api.context_for_user(extra_context={"confirmation_url": url}),
            EMAIL_VERIFICATION,
        )
    )
