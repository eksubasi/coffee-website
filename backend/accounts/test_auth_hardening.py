"""Tests for KAN-74: auth throttling, generic errors and password reset."""

import re
from datetime import timedelta
from unittest import mock

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

User = get_user_model()

COOKIE = settings.AUTH_REFRESH_COOKIE["key"]
PASSWORD = "Roast-and-Brew-2026"
NEW_PASSWORD = "Fresh-Grind-Pour-2027"


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def customer(db):
    return User.objects.create_user(email="ada@brewnook.dev", password=PASSWORD)


def login(api, email="ada@brewnook.dev", password=PASSWORD, ip="10.0.0.1"):
    return api.post(
        reverse("auth-login"),
        {"email": email, "password": password},
        format="json",
        REMOTE_ADDR=ip,
    )


def register(api, email, ip="10.0.0.1", password=PASSWORD):
    return api.post(
        reverse("auth-register"),
        {"email": email, "password": password},
        format="json",
        REMOTE_ADDR=ip,
    )


def request_reset(api, email):
    return api.post(reverse("auth-password-reset"), {"email": email}, format="json")


def confirm_reset(api, uid, token, new_password=NEW_PASSWORD):
    return api.post(
        reverse("auth-password-reset-confirm"),
        {"uid": uid, "token": token, "new_password": new_password},
        format="json",
    )


def reset_params(user):
    return urlsafe_base64_encode(force_bytes(user.pk)), default_token_generator.make_token(user)


def params_from_email(message):
    match = re.search(r"uid=([^&\s]+)&token=(\S+)", message.body)
    assert match, message.body
    return match.group(1), match.group(2)


# --- Throttling -------------------------------------------------------------


@pytest.mark.django_db
def test_sixth_failed_login_in_a_minute_is_throttled(api, customer):
    for _ in range(5):
        assert login(api, password="wrong-password").status_code == 401

    response = login(api, password="wrong-password")

    assert response.status_code == 429
    assert int(response["Retry-After"]) > 0


@pytest.mark.django_db
def test_login_is_throttled_per_email_across_ips(api, customer):
    for i in range(5):
        assert login(api, password="wrong", ip=f"10.0.1.{i}").status_code == 401

    # A new IP is still blocked for this account; email matching ignores case.
    response = login(api, email="ADA@brewnook.dev", password="wrong", ip="10.0.2.1")

    assert response.status_code == 429
    assert "Retry-After" in response


@pytest.mark.django_db
def test_login_is_throttled_per_ip_across_emails(api, customer):
    for i in range(5):
        assert login(api, email=f"nobody{i}@brewnook.dev", password="wrong").status_code == 401

    response = login(api)  # correct credentials, same IP

    assert response.status_code == 429


@pytest.mark.django_db
def test_login_throttle_does_not_affect_other_ips_and_emails(api, customer):
    for _ in range(5):
        login(api, email="other@brewnook.dev", password="wrong", ip="10.0.0.9")

    assert login(api, ip="10.0.0.10").status_code == 200


@pytest.mark.django_db
def test_login_ip_throttle_ignores_spoofed_forwarded_for(api, customer):
    for i in range(5):
        api.post(
            reverse("auth-login"),
            {"email": f"x{i}@brewnook.dev", "password": "wrong"},
            format="json",
            REMOTE_ADDR="10.0.0.1",
            HTTP_X_FORWARDED_FOR=f"203.0.113.{i}",
        )

    assert login(api, ip="10.0.0.1").status_code == 429


@pytest.mark.django_db
def test_fourth_registration_in_a_minute_from_one_ip_is_throttled(api):
    for i in range(3):
        assert register(api, f"user{i}@brewnook.dev").status_code == 201

    response = register(api, "user3@brewnook.dev")

    assert response.status_code == 429
    assert int(response["Retry-After"]) > 0
    assert not User.objects.filter(email="user3@brewnook.dev").exists()


# --- Generic error messages -------------------------------------------------


@pytest.mark.django_db
def test_login_error_is_identical_for_unknown_email_and_wrong_password(api, customer):
    unknown = login(api, email="ghost@brewnook.dev", ip="10.0.0.2")
    wrong = login(api, password="wrong-password", ip="10.0.0.3")

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


@pytest.mark.django_db
def test_login_error_is_generic_for_inactive_user(api, customer):
    customer.is_active = False
    customer.save()

    inactive = login(api, ip="10.0.0.2")
    unknown = login(api, email="ghost@brewnook.dev", ip="10.0.0.3")

    assert inactive.status_code == 401
    assert inactive.json() == unknown.json()


@pytest.mark.django_db
def test_register_duplicate_email_gives_generic_error(api, customer):
    response = register(api, "ADA@brewnook.dev")

    assert response.status_code == 400
    body = response.json()
    assert set(body) == {"detail"}
    assert "exist" not in body["detail"].lower()
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_register_duplicate_email_with_weak_password_reports_password(api, customer):
    """A weak password is reported the same way whether or not the email is taken."""
    taken = register(api, "ada@brewnook.dev", password="short", ip="10.0.0.2")
    free = register(api, "free@brewnook.dev", password="short", ip="10.0.0.3")

    assert taken.status_code == free.status_code == 400
    assert taken.json() == free.json()
    assert "password" in taken.json()


# --- Password reset request -------------------------------------------------


@pytest.mark.django_db
def test_password_reset_sends_single_email_with_link(api, customer):
    response = request_reset(api, "ada@brewnook.dev")

    assert response.status_code == 202
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["ada@brewnook.dev"]
    assert f"{settings.FRONTEND_URL}/reset-password?uid=" in message.body


@pytest.mark.django_db
def test_password_reset_unknown_email_returns_same_202(api, customer):
    known = request_reset(api, "ada@brewnook.dev")
    unknown = request_reset(api, "ghost@brewnook.dev")

    assert unknown.status_code == known.status_code == 202
    assert unknown.json() == known.json()
    assert len(mail.outbox) == 1  # only the real account got an email


@pytest.mark.django_db
def test_password_reset_inactive_user_gets_no_email(api, customer):
    customer.is_active = False
    customer.save()

    response = request_reset(api, "ada@brewnook.dev")

    assert response.status_code == 202
    assert mail.outbox == []


@pytest.mark.django_db
def test_password_reset_email_failure_still_returns_202(api, customer):
    with mock.patch("accounts.views.send_mail", side_effect=OSError("smtp down")):
        response = request_reset(api, "ada@brewnook.dev")

    assert response.status_code == 202


# --- Password reset confirm -------------------------------------------------


@pytest.mark.django_db
def test_password_reset_confirm_changes_password(api, customer):
    request_reset(api, "ada@brewnook.dev")
    uid, token = params_from_email(mail.outbox[0])

    response = confirm_reset(api, uid, token)

    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.check_password(NEW_PASSWORD)
    assert login(api, password=NEW_PASSWORD).status_code == 200


@pytest.mark.django_db
def test_password_reset_token_is_single_use(api, customer):
    uid, token = reset_params(customer)
    assert confirm_reset(api, uid, token).status_code == 200

    response = confirm_reset(api, uid, token, new_password="Another-Strong-Pass-99")

    assert response.status_code == 400
    customer.refresh_from_db()
    assert customer.check_password(NEW_PASSWORD)


@pytest.mark.django_db
def test_password_reset_expired_token_is_rejected(api, customer):
    uid, token = reset_params(customer)
    later = default_token_generator._now() + timedelta(
        seconds=settings.PASSWORD_RESET_TIMEOUT + 1
    )

    with mock.patch.object(default_token_generator, "_now", return_value=later):
        response = confirm_reset(api, uid, token)

    assert response.status_code == 400
    customer.refresh_from_db()
    assert customer.check_password(PASSWORD)


@pytest.mark.django_db
def test_password_reset_token_valid_just_before_expiry(api, customer):
    uid, token = reset_params(customer)
    later = default_token_generator._now() + timedelta(
        seconds=settings.PASSWORD_RESET_TIMEOUT - 60
    )

    with mock.patch.object(default_token_generator, "_now", return_value=later):
        response = confirm_reset(api, uid, token)

    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "uid,token",
    [
        ("bm90LWEtbnVtYmVy", "garbage-token"),  # uid decodes to a non-integer
        ("!!!", "garbage-token"),  # not base64
        ("OTk5OTk5", "garbage-token"),  # unknown user id 999999
        (None, "garbage-token"),  # valid uid, wrong token (filled in below)
    ],
)
def test_password_reset_invalid_uid_or_token_is_rejected(api, customer, uid, token):
    if uid is None:
        uid, _ = reset_params(customer)

    response = confirm_reset(api, uid, token)

    assert response.status_code == 400
    assert "detail" in response.json()
    customer.refresh_from_db()
    assert customer.check_password(PASSWORD)


@pytest.mark.django_db
@pytest.mark.parametrize("weak_password", ["short", "password123", "12345678901", "ada@brewnook.dev"])
def test_password_reset_enforces_password_rules(api, customer, weak_password):
    uid, token = reset_params(customer)

    response = confirm_reset(api, uid, token, new_password=weak_password)

    assert response.status_code == 400
    assert "new_password" in response.json()
    customer.refresh_from_db()
    assert customer.check_password(PASSWORD)
    # The token was not consumed by the failed attempt.
    assert confirm_reset(api, uid, token).status_code == 200


@pytest.mark.django_db
def test_password_reset_revokes_existing_refresh_tokens(api, customer):
    login(api)
    old_refresh = api.cookies[COOKIE].value
    customer.refresh_from_db()  # login updated last_login, which the token hashes
    uid, token = reset_params(customer)

    assert confirm_reset(api, uid, token).status_code == 200

    api.cookies[COOKIE] = old_refresh
    response = api.post(reverse("auth-refresh"))
    assert response.status_code == 401
