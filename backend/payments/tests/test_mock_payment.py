import logging
from datetime import date

import pytest
from django.db import connection
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from payments.models import PaymentToken

PAN = "4242424242424242"
CVV = "737"
NEXT_YEAR = (date.today().year + 1) % 100

pytestmark = pytest.mark.django_db


def payload(**overrides):
    data = {
        "card_number": "4242 4242 4242 4242",
        "expiry": f"12/{NEXT_YEAR:02d}",
        "cvv": CVV,
        "holder": "Ada Brew",
    }
    data.update(overrides)
    return data


def client_for(role=User.Role.CUSTOMER):
    user = User.objects.create_user(email=f"{role}@pay.test", password="x", role=role)
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


def pay(client, **overrides):
    return client.post(reverse("payments-mock"), payload(**overrides), format="json")


def test_valid_card_is_approved_and_tokenised():
    client, user = client_for()

    response = pay(client)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "approved"
    assert body["last4"] == "4242"
    token = PaymentToken.objects.get(user=user)
    assert token.last4 == "4242"
    assert body["payment_token"] == token.token
    assert len(token.token) == 64


def test_response_never_contains_pan_or_cvv():
    client, _ = client_for()

    content = pay(client).content.decode()

    assert PAN not in content
    assert CVV not in content
    assert "card_number" not in content
    assert "cvv" not in content


def test_raw_pan_and_cvv_are_not_persisted_anywhere():
    client, _ = client_for()
    pay(client)

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM payments_paymenttoken")
        rows = cursor.fetchall()

    stored = " ".join(str(value) for row in rows for value in row)
    assert rows
    assert PAN not in stored
    assert CVV not in stored


def test_pan_and_cvv_are_not_logged(caplog):
    client, _ = client_for()

    with caplog.at_level(logging.DEBUG):
        pay(client)
        pay(client, card_number="4242424242424241")  # rejected request too

    assert PAN not in caplog.text
    assert "4242424242424241" not in caplog.text
    assert CVV not in caplog.text


def test_same_card_reuses_existing_token():
    client, user = client_for()

    first = pay(client).json()["payment_token"]
    second = pay(client, card_number=PAN).json()["payment_token"]

    assert first == second
    assert PaymentToken.objects.filter(user=user).count() == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("card_number", "4242424242424241"),  # fails Luhn
        ("card_number", "1234"),  # too short
        ("card_number", "4242-abcd-4242-4242"),
        ("expiry", "13/30"),
        ("expiry", "1/30"),
        ("expiry", "01/20"),  # expired
        ("cvv", "12"),
        ("cvv", "12a"),
        ("holder", ""),
    ],
)
def test_invalid_input_is_rejected_without_echoing_it(field, value):
    client, _ = client_for()

    response = pay(client, **{field: value})

    assert response.status_code == 400
    assert field in response.json()
    if value:
        assert value not in response.content.decode()
    assert PaymentToken.objects.count() == 0


@pytest.mark.parametrize(
    "role",
    [User.Role.SALES_MANAGER, User.Role.PRODUCT_MANAGER, User.Role.SUPPORT_AGENT],
)
def test_only_customers_can_pay(role):
    client, _ = client_for(role)

    assert pay(client).status_code == 403


def test_anonymous_cannot_pay():
    assert APIClient().post(reverse("payments-mock"), payload(), format="json").status_code == 401


# --- KAN-53: edge cases -------------------------------------------------------

AMEX = "378282246310005"  # 15-digit test number, passes Luhn


def test_fifteen_digit_card_with_four_digit_cvv_is_approved():
    client, _ = client_for()

    response = pay(client, card_number=AMEX, cvv="1234")

    assert response.status_code == 201
    assert response.json()["last4"] == "0005"


def test_same_card_for_two_customers_creates_separate_token_rows():
    first_client, first_user = client_for()
    second_user = User.objects.create_user(email="second@pay.test", password="x")
    second_client = APIClient()
    second_client.force_authenticate(user=second_user)

    pay(first_client)
    pay(second_client)

    assert PaymentToken.objects.filter(user=first_user).count() == 1
    assert PaymentToken.objects.filter(user=second_user).count() == 1


def test_token_depends_on_secret_key(settings):
    from payments.cards import card_token

    settings.SECRET_KEY = "secret-one"
    first = card_token(PAN)
    settings.SECRET_KEY = "secret-two"

    assert card_token(PAN) != first


@pytest.mark.parametrize("missing", ["card_number", "expiry", "cvv", "holder"])
def test_missing_field_is_rejected(missing):
    client, _ = client_for()
    data = payload()
    del data[missing]

    response = client.post(reverse("payments-mock"), data, format="json")

    assert response.status_code == 400
    assert missing in response.json()


def test_get_is_not_allowed():
    client, _ = client_for()

    assert client.get(reverse("payments-mock")).status_code == 405
