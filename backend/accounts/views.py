from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


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


class RegisterView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

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
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

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
