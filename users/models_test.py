"""Tests for user models"""
import factory
import pytest
from django.core.exceptions import ValidationError
from django.db import transaction

from affiliate.factories import AffiliateFactory
from courseware.factories import CoursewareUserFactory, OpenEdxApiAuthFactory
from users.factories import UserFactory
from users.models import LegalAddress, User

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "create_func,exp_staff,exp_superuser,exp_is_active",  # noqa: PT006
    [
        [User.objects.create_user, False, False, False],  # noqa: PT007
        [User.objects.create_superuser, True, True, True],  # noqa: PT007
    ],
)
@pytest.mark.parametrize("password", [None, "pass"])
def test_create_user(create_func, exp_staff, exp_superuser, exp_is_active, password):
    """Test creating a user"""
    username = "user1"
    email = "uSer@EXAMPLE.com"
    name = "Jane Doe"
    with transaction.atomic():
        user = create_func(username, email=email, name=name, password=password)

    assert user.username == username
    assert user.email == "uSer@example.com"
    assert user.name == name
    assert user.get_full_name() == name
    assert user.is_staff is exp_staff
    assert user.is_superuser is exp_superuser
    assert user.is_active is exp_is_active
    if password is not None:
        assert user.check_password(password)

    assert LegalAddress.objects.filter(user=user).exists()


def test_create_user_affiliate():
    """create_user should create a new affiliate tracking record if an affiliate id was passed in the kwargs"""
    affiliate = AffiliateFactory.create()
    with transaction.atomic():
        user = User.objects.create_user(
            "username1",
            email="a@b.com",
            name="Jane Doe",
            password="asdfghjkl1",  # noqa: S106
            affiliate_id=affiliate.id,
        )
    affiliate_referral_action = user.affiliate_user_actions.first()
    assert affiliate_referral_action is not None
    assert affiliate_referral_action.affiliate == affiliate
    assert affiliate_referral_action.created_user == user


@pytest.mark.parametrize(
    "kwargs",
    [
        {"is_staff": False},
        {"is_superuser": False},
        {"is_staff": False, "is_superuser": False},
    ],
)
def test_create_superuser_error(kwargs):
    """Test creating a user"""
    with pytest.raises(ValueError):  # noqa: PT011
        User.objects.create_superuser(
            username=None,
            email="uSer@EXAMPLE.com",
            name="Jane Doe",
            password="abc",  # noqa: S106
            **kwargs,
        )


@pytest.mark.parametrize(
    "field, value, is_valid",  # noqa: PT006
    [
        ["country", "US", True],  # noqa: PT007
        ["country", "United States", False],  # noqa: PT007
        ["state_or_territory", "US-MA", True],  # noqa: PT007
        ["state_or_territory", "MA", False],  # noqa: PT007
        ["state_or_territory", "Massachusets", False],  # noqa: PT007
    ],
)
def test_legal_address_validation(field, value, is_valid):
    """Verify legal address validation"""
    address = LegalAddress()

    setattr(address, field, value)

    with pytest.raises(ValidationError) as exc:
        address.clean_fields()

    if is_valid:
        assert field not in exc.value.error_dict
    else:
        assert field in exc.value.error_dict


@pytest.mark.django_db
def test_faulty_user_qset():
    """User.faulty_courseware_users should return a User queryset that contains incorrectly configured active Users"""
    users = UserFactory.create_batch(5)
    # An inactive user should not be returned even if they lack auth and courseware user records
    UserFactory.create(is_active=False)
    good_users = users[0:2]
    expected_faulty_users = users[2:]
    OpenEdxApiAuthFactory.create_batch(
        3,
        user=factory.Iterator(good_users + [users[3]]),  # noqa: RUF005
    )
    CoursewareUserFactory.create_batch(
        3,
        user=factory.Iterator(good_users + [users[4]]),  # noqa: RUF005
    )

    assert set(User.faulty_courseware_users.values_list("id", flat=True)) == {
        user.id for user in expected_faulty_users
    }
