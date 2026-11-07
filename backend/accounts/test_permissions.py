"""Role matrix tests (KAN-38).

Sample endpoints are defined here and mounted only for this module via
``pytest.mark.urls`` so the real API surface is not changed.
"""

import pytest
from django.urls import path, reverse
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import (
    IsCustomer,
    IsProductManager,
    IsSalesManager,
    IsSupportAgent,
)

ROLE_PERMISSIONS = {
    User.Role.CUSTOMER: IsCustomer,
    User.Role.SALES_MANAGER: IsSalesManager,
    User.Role.PRODUCT_MANAGER: IsProductManager,
    User.Role.SUPPORT_AGENT: IsSupportAgent,
}


def _sample_view(permission):
    class SampleView(APIView):
        permission_classes = [permission]

        def get(self, request):
            return Response({"ok": True})

    return SampleView.as_view()


class DefaultPermissionView(APIView):
    """No permission_classes: falls back to DEFAULT_PERMISSION_CLASSES."""

    def get(self, request):
        return Response({"ok": True})


class SharedView(APIView):
    permission_classes = [IsSalesManager | IsProductManager]

    def get(self, request):
        return Response({"ok": True})


urlpatterns = [
    path(f"sample/{role}", _sample_view(permission), name=f"sample-{role}")
    for role, permission in ROLE_PERMISSIONS.items()
] + [
    path("sample/default", DefaultPermissionView.as_view(), name="sample-default"),
    path("sample/shared", SharedView.as_view(), name="sample-shared"),
]

pytestmark = [pytest.mark.django_db, pytest.mark.urls(__name__)]

ALL_ROLES = list(ROLE_PERMISSIONS)


def client_for(role, **extra):
    user = User.objects.create_user(
        email=f"{role}@perm.test", password="x", role=role, **extra
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.parametrize("role", ALL_ROLES)
def test_role_can_access_its_own_endpoint(role):
    response = client_for(role).get(reverse(f"sample-{role}"))

    assert response.status_code == 200


@pytest.mark.parametrize(
    "role,endpoint_role",
    [(r, e) for r in ALL_ROLES for e in ALL_ROLES if r != e],
)
def test_role_gets_403_on_other_roles_endpoints(role, endpoint_role):
    response = client_for(role).get(reverse(f"sample-{endpoint_role}"))

    assert response.status_code == 403


@pytest.mark.parametrize("endpoint_role", ALL_ROLES)
def test_anonymous_gets_401_on_role_endpoints(endpoint_role):
    response = APIClient().get(reverse(f"sample-{endpoint_role}"))

    assert response.status_code == 401


def test_inactive_user_is_denied_even_with_matching_role():
    client = client_for(User.Role.PRODUCT_MANAGER, is_active=False)

    response = client.get(reverse(f"sample-{User.Role.PRODUCT_MANAGER}"))

    assert response.status_code == 403


def test_superuser_without_matching_role_is_denied():
    admin = User.objects.create_superuser(email="admin@perm.test", password="x")
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get(reverse(f"sample-{User.Role.SALES_MANAGER}"))

    assert response.status_code == 403


def test_default_permission_requires_authentication():
    assert APIClient().get(reverse("sample-default")).status_code == 401
    assert client_for(User.Role.CUSTOMER).get(reverse("sample-default")).status_code == 200


@pytest.mark.parametrize(
    "role,expected",
    [
        (User.Role.SALES_MANAGER, 200),
        (User.Role.PRODUCT_MANAGER, 200),
        (User.Role.CUSTOMER, 403),
        (User.Role.SUPPORT_AGENT, 403),
    ],
)
def test_permissions_can_be_combined_for_shared_endpoints(role, expected):
    assert client_for(role).get(reverse("sample-shared")).status_code == expected
