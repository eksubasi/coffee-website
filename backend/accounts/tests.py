import pytest
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


def test_email_is_the_login_field():
    assert User.USERNAME_FIELD == "email"
    assert "username" not in {field.name for field in User._meta.get_fields()}


def test_full_name_is_the_only_name_field():
    field_names = {field.name for field in User._meta.get_fields()}

    assert "full_name" in field_names
    assert "first_name" not in field_names
    assert "last_name" not in field_names


@pytest.mark.django_db
def test_user_can_authenticate_with_email():
    User.objects.create_user(email="login@brewnook.dev", password="s3cret-pass")

    user = authenticate(email="login@brewnook.dev", password="s3cret-pass")

    assert user is not None
    assert user.email == "login@brewnook.dev"


@pytest.mark.django_db
def test_role_defaults_to_customer():
    user = User.objects.create_user(
        email="new@brewnook.dev", password="x", full_name="Ada Brew"
    )

    assert user.get_full_name() == "Ada Brew"
    assert user.role == User.Role.CUSTOMER
    assert user.tax_id == ""
    assert user.home_address == ""


@pytest.mark.django_db
def test_create_user_normalises_email_domain():
    user = User.objects.create_user(email="Alice@BrewNook.DEV", password="x")

    assert user.email == "Alice@brewnook.dev"


def test_create_user_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="x")


@pytest.mark.django_db
def test_create_superuser_sets_staff_and_superuser_flags():
    admin = User.objects.create_superuser(email="admin@brewnook.dev", password="x")

    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.check_password("x")


def test_create_superuser_rejects_non_staff():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="admin@brewnook.dev", password="x", is_staff=False
        )

