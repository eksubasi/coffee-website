"""Card helpers. Raw card numbers and CVVs must never be stored or logged."""

import calendar
import hashlib
import re
from datetime import date

from django.conf import settings

_EXPIRY_RE = re.compile(r"^(?P<month>\d{2})/(?P<year>\d{2})$")


def normalise_card_number(value: str) -> str:
    """Remove spaces and dashes commonly typed into card fields."""
    return re.sub(r"[\s-]", "", value or "")


def luhn_is_valid(card_number: str) -> bool:
    if not card_number.isdigit():
        return False
    total = 0
    for index, char in enumerate(reversed(card_number)):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def parse_expiry(value: str) -> tuple[int, int] | None:
    """Parse ``MM/YY`` into ``(month, four_digit_year)``; ``None`` if malformed."""
    match = _EXPIRY_RE.match(value or "")
    if not match:
        return None
    month = int(match["month"])
    if not 1 <= month <= 12:
        return None
    return month, 2000 + int(match["year"])


def is_expired(month: int, year: int, today: date | None = None) -> bool:
    """A card is valid through the last day of its expiry month."""
    today = today or date.today()
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day) < today


def card_token(card_number: str) -> str:
    """Deterministic, non-reversible token: sha256(card_number + SECRET_KEY)."""
    return hashlib.sha256((card_number + settings.SECRET_KEY).encode()).hexdigest()
