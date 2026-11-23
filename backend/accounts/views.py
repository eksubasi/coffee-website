import logging

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .throttling import LoginEmailThrottle, LoginIPThrottle, RegisterIPThrottle

logger = logging.getLogger(__name__)
User = get_user_model()

# Generic messages: none of them reveal whether an account exists.
LOGIN_FAILED_MESSAGE = "Invalid email or password."
REGISTER_FAILED_MESSAGE = "Registration could not be completed with the provided details."
PASSWORD_RESET_REQUESTED_MESSAGE = (
    "If an account exists for this email, a password reset link has been sent."
)
PASSWORD_RESET_INVALID_MESSAGE = "The password reset link is invalid or has expired."


def _set_refresh_cookie(response, refresh_token):
    cookie = settings.AUTH_REFRESH_COOKIE
    response.set_cookie(
        cookie["key"],
        str(refresh_token),
        max_age=int(jwt_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
        path=cookie["path"],
        httponly=cookie["httponly"],
        secure=cookie["secure"],
        samesite=cookie["samesite"],
    )


def _delete_refresh_cookie(response):
    cookie = settings.AUTH_REFRESH_COOKIE
    response.delete_cookie(cookie["key"], path=cookie["path"], samesite=cookie["samesite"])


def _invalid_refresh_response():
    response = Response(
        {"detail": "Refresh token is missing or invalid."},
        status=status.HTTP_401_UNAUTHORIZED,
    )
    _delete_refresh_cookie(response)
    return response


def _register_failed_response():
    return Response({"detail": REGISTER_FAILED_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [RegisterIPThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Checked only after every field validated, so a taken email and a
        # weak password cannot be told apart by which error comes back.
        email = serializer.validated_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            return _register_failed_response()
        try:
            with transaction.atomic():
                user = serializer.save()
        except IntegrityError:
            return _register_failed_response()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginIPThrottle, LoginEmailThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": LOGIN_FAILED_MESSAGE},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # SimpleJWT's UPDATE_LAST_LOGIN only applies to its own serializers.
        update_last_login(None, user)
        refresh = RefreshToken.for_user(user)
        response = Response(
            {"access": str(refresh.access_token), "user": UserSerializer(user).data}
        )
        _set_refresh_cookie(response, refresh)
        return response


class RefreshView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        raw_token = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE["key"])
        if not raw_token:
            return _invalid_refresh_response()

        serializer = TokenRefreshSerializer(data={"refresh": raw_token})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken, ValidationError):
            return _invalid_refresh_response()

        response = Response({"access": serializer.validated_data["access"]})
        rotated = serializer.validated_data.get("refresh")
        if rotated:
            _set_refresh_cookie(response, rotated)
        return response


class LogoutView(APIView):
    """Blacklist the refresh token (if any) and clear the cookie.

    Allowed without a valid access token so an expired session can still
    log out.
    """

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        raw_token = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE["key"])
        if raw_token:
            try:
                RefreshToken(raw_token).blacklist()
            except TokenError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        _delete_refresh_cookie(response)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class PasswordResetRequestView(APIView):
    """Send a single-use reset link. Always 202, whether or not the email exists."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is not None and user.has_usable_password():
            _send_password_reset_email(user)

        return Response(
            {"detail": PASSWORD_RESET_REQUESTED_MESSAGE}, status=status.HTTP_202_ACCEPTED
        )


def _send_password_reset_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?uid={uid}&token={token}"
    minutes = settings.PASSWORD_RESET_TIMEOUT // 60
    body = (
        "A password reset was requested for your Brewnook account.\n\n"
        f"Open this link to choose a new password (valid for {minutes} minutes, "
        f"usable once):\n{link}\n\n"
        "If you did not request this, you can ignore this email."
    )
    try:
        send_mail("Reset your Brewnook password", body, None, [user.email])
    except Exception:
        # Never let a delivery failure change the response (it would reveal
        # that the account exists).
        logger.exception("Failed to send password reset email to user %s", user.pk)


class PasswordResetConfirmView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = _user_from_uid(data["uid"])
        # The default token generator hashes the password and last_login into
        # the token, so it stops working once the password changes
        # (single use) and after PASSWORD_RESET_TIMEOUT (expiry).
        if user is None or not default_token_generator.check_token(user, data["token"]):
            return Response(
                {"detail": PASSWORD_RESET_INVALID_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(data["new_password"], user=user)
        except DjangoValidationError as exc:
            return Response(
                {"new_password": list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(data["new_password"])
        user.save(update_fields=["password"])
        _blacklist_refresh_tokens(user)
        return Response({"detail": "Your password has been reset."})


def _user_from_uid(uid):
    try:
        pk = force_str(urlsafe_base64_decode(uid))
        return User.objects.get(pk=pk, is_active=True)
    except (TypeError, ValueError, OverflowError, DjangoValidationError, User.DoesNotExist):
        return None


def _blacklist_refresh_tokens(user):
    """Log the user out everywhere after a password reset."""
    for outstanding in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=outstanding)
