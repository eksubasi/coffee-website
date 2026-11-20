from datetime import date

import pytest

from payments.cards import card_token, is_expired, luhn_is_valid, parse_expiry


@pytest.mark.parametrize(
    "number,valid",
    [
        ("4242424242424242", True),
        ("4242424242424241", False),
        ("79927398713", True),  # classic Luhn example
        ("79927398710", False),
        ("4242abcd42424242", False),
    ],
)
def test_luhn(number, valid):
    assert luhn_is_valid(number) is valid


@pytest.mark.parametrize(
    "value,expected",
    [
        ("01/30", (1, 2030)),
        ("12/27", (12, 2027)),
        ("13/27", None),
        ("00/27", None),
        ("1/27", None),
        ("01/2027", None),
        ("01-27", None),
    ],
)
def test_parse_expiry(value, expected):
    assert parse_expiry(value) == expected


def test_card_is_valid_through_end_of_expiry_month():
    assert is_expired(11, 2026, today=date(2026, 11, 30)) is False
    assert is_expired(11, 2026, today=date(2026, 12, 1)) is True


def test_card_token_is_sha256_of_number_plus_secret(settings):
    import hashlib

    settings.SECRET_KEY = "test-secret"
    expected = hashlib.sha256(b"4242424242424242test-secret").hexdigest()

    assert card_token("4242424242424242") == expected
    assert len(card_token("4242424242424242")) == 64
