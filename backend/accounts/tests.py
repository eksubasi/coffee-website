import pytest
from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command

User = get_user_model()

SEEDED_EMAILS = {
    "customer@brewnook.dev",
    "sales@brewnook.dev",
    "product@brewnook.dev",
    "support@brewnook.dev",
}


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


@pytest.mark.django_db
def test_seed_users_is_idempotent(monkeypatch, capsys):
    monkeypatch.setenv("DEMO_PASSWORD", "seed-test-password")

    call_command("seed_users")
    call_command("seed_users")
    output = capsys.readouterr().out

    users = User.objects.filter(email__in=SEEDED_EMAILS)
    assert users.count() == 4
    assert User.objects.count() == 4
    assert {user.role for user in users} == set(User.Role.values)
    assert all(user.check_password("seed-test-password") for user in users)
    assert "seed-test-password" not in output
