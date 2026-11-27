"""Throttles for the unauthenticated auth endpoints.

Rates live in ``REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]``. Every request to
a throttled view counts, successful or not. When a limit is hit DRF responds
with 429 and a ``Retry-After`` header.
"""

import hashlib

from rest_framework.throttling import SimpleRateThrottle


class _IPThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class LoginIPThrottle(_IPThrottle):
    scope = "login_ip"


class RegisterIPThrottle(_IPThrottle):
    scope = "register_ip"


class LoginEmailThrottle(SimpleRateThrottle):
    """Limits attempts per target account, regardless of the client IP."""

    scope = "login_email"

    def get_cache_key(self, request, view):
        email = request.data.get("email") if hasattr(request.data, "get") else None
        if not isinstance(email, str) or not email.strip():
            return None
        # Hash so arbitrary user input never ends up raw in a cache key.
        ident = hashlib.sha256(email.strip().lower().encode()).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": ident}
