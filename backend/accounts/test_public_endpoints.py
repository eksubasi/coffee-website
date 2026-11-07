"""Public endpoints must stay reachable without login despite the
IsAuthenticated default (KAN-38)."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    ["/api/products/", "/api/categories/", "/api/health"],
)
def test_public_get_endpoints_allow_anonymous(url):
    assert APIClient().get(url).status_code == 200


@pytest.mark.parametrize(
    "name,expected_status",
    [
        ("auth-register", 400),  # empty body -> validation error, not 401/403
        ("auth-login", 400),
        ("auth-refresh", 401),  # view's own "refresh token missing" response
        ("auth-logout", 204),
    ],
)
def test_auth_entry_points_do_not_require_access_token(name, expected_status):
    response = APIClient().post(reverse(name), {}, format="json")

    assert response.status_code == expected_status


def test_me_requires_authentication():
    assert APIClient().get(reverse("auth-me")).status_code == 401
