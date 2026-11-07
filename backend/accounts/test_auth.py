import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()

COOKIE = settings.AUTH_REFRESH_COOKIE["key"]
STRONG_PASSWORD = "Roast-and-Brew-2026"


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        email="ada@brewnook.dev", password=STRONG_PASSWORD, full_name="Ada Brew"
    )


def login(api, email="ada@brewnook.dev", password=STRONG_PASSWORD):
    return api.post(
        reverse("auth-login"), {"email": email, "password": password}, format="json"
    )


@pytest.mark.django_db
def test_register_creates_customer_with_hashed_password(api):
    response = api.post(
        reverse("auth-register"),
        {
            "email": "new@BrewNook.dev",
            "password": STRONG_PASSWORD,
            "full_name": "New Customer",
            "role": "sales_manager",
        },
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@brewnook.dev"
    assert body["role"] == "customer"
    assert "password" not in body
    user = User.objects.get(email="new@brewnook.dev")
    assert user.role == User.Role.CUSTOMER
    assert user.password.startswith("argon2")


@pytest.mark.django_db
def test_register_rejects_duplicate_email_case_insensitively(api, customer):
    response = api.post(
        reverse("auth-register"),
        {"email": "ADA@brewnook.dev", "password": STRONG_PASSWORD},
        format="json",
    )

    assert response.status_code == 400
    assert "email" in response.json()
    assert User.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("weak_password", ["short", "password123", "12345678901"])
def test_register_rejects_weak_password(api, weak_password):
    response = api.post(
        reverse("auth-register"),
        {"email": "weak@brewnook.dev", "password": weak_password},
        format="json",
    )

    assert response.status_code == 400
    assert "password" in response.json()
    assert not User.objects.filter(email="weak@brewnook.dev").exists()


@pytest.mark.django_db
def test_login_returns_access_token_and_httponly_refresh_cookie(api, customer):
    response = login(api)

    assert response.status_code == 200
    body = response.json()
    assert body["access"]
    assert "refresh" not in body
    assert body["user"]["email"] == customer.email
    cookie = response.cookies[COOKIE]
    assert cookie.value
    assert cookie["httponly"]
    assert cookie["path"] == "/api/auth/"


@pytest.mark.django_db
def test_login_updates_last_login(api, customer):
    assert customer.last_login is None

    login(api)

    customer.refresh_from_db()
    assert customer.last_login is not None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "email,password",
    [("ada@brewnook.dev", "wrong-password"), ("nobody@brewnook.dev", STRONG_PASSWORD)],
)
def test_login_rejects_bad_credentials(api, customer, email, password):
    response = login(api, email=email, password=password)

    assert response.status_code == 401
    assert "access" not in response.json()
    assert COOKIE not in response.cookies


@pytest.mark.django_db
def test_me_requires_authentication(api):
    response = api.get(reverse("auth-me"))

    assert response.status_code == 401


@pytest.mark.django_db
def test_me_returns_current_user_with_access_token(api, customer):
    access = login(api).json()["access"]

    api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    response = api.get(reverse("auth-me"))

    assert response.status_code == 200
    assert response.json()["email"] == customer.email
    assert response.json()["role"] == "customer"


@pytest.mark.django_db
def test_refresh_issues_new_access_token_and_rotates_cookie(api, customer):
    old_refresh = login(api).cookies[COOKIE].value

    response = api.post(reverse("auth-refresh"))

    assert response.status_code == 200
    assert response.json()["access"]
    new_refresh = response.cookies[COOKIE].value
    assert new_refresh and new_refresh != old_refresh

    # The rotated-out token is blacklisted and cannot be reused.
    api.cookies[COOKIE] = old_refresh
    assert api.post(reverse("auth-refresh")).status_code == 401


@pytest.mark.django_db
def test_refresh_without_cookie_is_rejected(api):
    response = api.post(reverse("auth-refresh"))

    assert response.status_code == 401


@pytest.mark.django_db
def test_logout_clears_cookie_and_blacklists_refresh_token(api, customer):
    refresh = login(api).cookies[COOKIE].value

    response = api.post(reverse("auth-logout"))

    assert response.status_code == 204
    assert response.cookies[COOKIE].value == ""
    api.cookies[COOKIE] = refresh
    assert api.post(reverse("auth-refresh")).status_code == 401


# --- KAN-53: edge cases -------------------------------------------------------


@pytest.mark.django_db
def test_inactive_user_cannot_log_in(api, customer):
    customer.is_active = False
    customer.save()

    response = login(api)

    assert response.status_code == 401
    assert COOKIE not in response.cookies


@pytest.mark.django_db
def test_access_token_cannot_be_used_as_refresh_token(api, customer):
    access = login(api).json()["access"]
    api.cookies[COOKIE] = access

    assert api.post(reverse("auth-refresh")).status_code == 401


@pytest.mark.django_db
def test_refresh_token_cannot_be_used_as_access_token(api, customer):
    refresh = login(api).cookies[COOKIE].value

    api.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh}")

    assert api.get(reverse("auth-me")).status_code == 401


@pytest.mark.django_db
def test_register_ignores_privilege_fields(api):
    response = api.post(
        reverse("auth-register"),
        {
            "email": "sneaky@brewnook.dev",
            "password": STRONG_PASSWORD,
            "is_staff": True,
            "is_superuser": True,
        },
        format="json",
    )

    assert response.status_code == 201
    user = User.objects.get(email="sneaky@brewnook.dev")
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_tampered_access_token_is_rejected(api, customer):
    access = login(api).json()["access"]
    tampered = access[:-2] + ("AA" if access[-2:] != "AA" else "BB")

    api.credentials(HTTP_AUTHORIZATION=f"Bearer {tampered}")

    assert api.get(reverse("auth-me")).status_code == 401
