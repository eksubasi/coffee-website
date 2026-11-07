"""Local development settings."""

from .base import *  # noqa: F403
from .base import env

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Local development runs over plain HTTP.
AUTH_REFRESH_COOKIE = {**AUTH_REFRESH_COOKIE, "secure": False}  # noqa: F405
