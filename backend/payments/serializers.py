from rest_framework import serializers

from .cards import is_expired, luhn_is_valid, normalise_card_number, parse_expiry


class MockPaymentSerializer(serializers.Serializer):
    """Validates card input. Error messages never echo the submitted values."""

    card_number = serializers.CharField(write_only=True, max_length=32)
    expiry = serializers.CharField(write_only=True, max_length=5)
    cvv = serializers.CharField(write_only=True, max_length=4, min_length=3)
    holder = serializers.CharField(max_length=100)

    def validate_card_number(self, value):
        number = normalise_card_number(value)
        if not number.isdigit() or not 12 <= len(number) <= 19:
            raise serializers.ValidationError("Card number must contain 12 to 19 digits.")
        if not luhn_is_valid(number):
            raise serializers.ValidationError("Card number is invalid.")
        return number

    def validate_expiry(self, value):
        parsed = parse_expiry(value)
        if parsed is None:
            raise serializers.ValidationError("Expiry must be in MM/YY format.")
        if is_expired(*parsed):
            raise serializers.ValidationError("Card has expired.")
        return value

    def validate_cvv(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("CVV must be 3 or 4 digits.")
        return value
