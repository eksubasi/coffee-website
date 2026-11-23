from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "tax_id", "home_address", "role"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Customer self-registration. The role is always ``customer``."""

    password = serializers.CharField(
        write_only=True, trim_whitespace=False, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = ["email", "password", "full_name", "tax_id", "home_address"]
        extra_kwargs = {
            # Uniqueness is checked case-insensitively in RegisterView, after
            # all field validation, so that the response never reveals
            # whether an email is already registered.
            "email": {"validators": []},
        }

    def validate_email(self, value):
        return User.objects.normalize_email(value)

    def validate(self, attrs):
        password = attrs.get("password")
        candidate = User(**{k: v for k, v in attrs.items() if k != "password"})
        try:
            validate_password(password, user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(role=User.Role.CUSTOMER, **validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False, style={"input_type": "password"})


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True, trim_whitespace=False, style={"input_type": "password"}
    )
