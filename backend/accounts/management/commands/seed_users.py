import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

DEFAULT_DEMO_PASSWORD = "brewnook-demo"


def demo_users():
    User = get_user_model()
    return [
        ("customer@brewnook.dev", "Demo Customer", User.Role.CUSTOMER),
        ("sales@brewnook.dev", "Demo Sales Manager", User.Role.SALES_MANAGER),
        ("product@brewnook.dev", "Demo Product Manager", User.Role.PRODUCT_MANAGER),
        ("support@brewnook.dev", "Demo Support Agent", User.Role.SUPPORT_AGENT),
    ]


class Command(BaseCommand):
    help = (
        "Create one demo user per role if missing. Existing users are left "
        "unchanged. The password is read from DEMO_PASSWORD."
    )

    def handle(self, *args, **options):
        User = get_user_model()
        password = os.environ.get("DEMO_PASSWORD") or DEFAULT_DEMO_PASSWORD

        created_count = 0
        for email, full_name, role in demo_users():
            if User.objects.filter(email=email).exists():
                self.stdout.write(f"exists:  {email} ({role})")
                continue
            User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role=role,
            )
            created_count += 1
            self.stdout.write(f"created: {email} ({role})")

        self.stdout.write(self.style.SUCCESS(f"Demo users created: {created_count}"))
