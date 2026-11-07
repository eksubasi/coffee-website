"""Role-based DRF permission classes.

Each class allows only authenticated, active users whose ``role`` matches.
Superusers get no implicit bypass: the role field is the single source of
truth for API access. Combine classes with ``|`` when an endpoint is shared
between roles, e.g. ``permission_classes = [IsSalesManager | IsProductManager]``.
"""

from rest_framework.permissions import BasePermission

from .models import User


class HasRole(BasePermission):
    role: str = ""
    message = "You do not have the required role for this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and getattr(user, "role", None) == self.role
        )


class IsCustomer(HasRole):
    role = User.Role.CUSTOMER


class IsSalesManager(HasRole):
    role = User.Role.SALES_MANAGER


class IsProductManager(HasRole):
    role = User.Role.PRODUCT_MANAGER


class IsSupportAgent(HasRole):
    role = User.Role.SUPPORT_AGENT
