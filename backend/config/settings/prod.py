"""Production settings. All hosts and origins must come from the environment."""

from .base import *  # noqa: F403
from .base import BASE_DIR, env
from .base import MIDDLEWARE as BASE_MIDDLEWARE

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="core.email_backends.ResendEmailBackend",
)

# Serve collected static files in production.
MIDDLEWARE = [
    BASE_MIDDLEWARE[0],
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *BASE_MIDDLEWARE[1:],
]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[],
)

# Frontend and backend may be hosted on separate domains.
AUTH_REFRESH_COOKIE = {
    **AUTH_REFRESH_COOKIE,  # noqa: F405
    "samesite": env("AUTH_REFRESH_COOKIE_SAMESITE", default="None"),
    "secure": True,
}

SESSION_COOKIE_SAMESITE = env(
    "SESSION_COOKIE_SAMESITE",
    default="None",
)
CSRF_COOKIE_SAMESITE = env(
    "CSRF_COOKIE_SAMESITE",
    default="None",
)