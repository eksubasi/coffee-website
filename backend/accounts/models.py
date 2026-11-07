from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """Brewnook user, identified by email address."""

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        SALES_MANAGER = "sales_manager", "Sales manager"
        PRODUCT_MANAGER = "product_manager", "Product manager"
        SUPPORT_AGENT = "support_agent", "Support agent"

    username = None
    # Single name source: full_name replaces first_name / last_name.
    first_name = None
    last_name = None
    email = models.EmailField("email address", unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    # Left blank for staff roles such as managers and support agents.
    tax_id = models.CharField(max_length=11, blank=True)
    home_address = models.TextField(blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name or self.email
