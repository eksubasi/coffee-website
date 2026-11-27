"""KAN-71: manage.py demo_reset puts the database into the demo starting state."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from accounts.models import User
from catalog.models import Product
from orders.models import Order
from reviews.models import Rating
from reviews.services import has_received

DEMO_EMAILS = {
    "customer@brewnook.dev": User.Role.CUSTOMER,
    "sales@brewnook.dev": User.Role.SALES_MANAGER,
    "product@brewnook.dev": User.Role.PRODUCT_MANAGER,
    "support@brewnook.dev": User.Role.SUPPORT_AGENT,
}

pytestmark = pytest.mark.django_db


def run_reset():
    call_command("demo_reset", stdout=StringIO())


@override_settings(DEBUG=True)
def test_creates_one_account_per_role_with_demo_password():
    run_reset()
    for email, role in DEMO_EMAILS.items():
        user = User.objects.get(email=email)
        assert user.role == role
        assert user.check_password("brewnook-demo")


@override_settings(DEBUG=True)
def test_customer_has_one_delivered_order_so_rating_is_allowed():
    run_reset()
    customer = User.objects.get(email="customer@brewnook.dev")
    orders = Order.objects.filter(user=customer)
    assert orders.count() == 1
    order = orders.get()
    assert order.status == Order.Status.DELIVERED
    assert order.invoice is not None
    product = order.items.get().product
    assert has_received(customer, product)


@override_settings(DEBUG=True)
def test_running_twice_gives_the_same_state():
    run_reset()
    customer = User.objects.get(email="customer@brewnook.dev")
    product = Product.objects.get(model="DB-ETH-250")
    Rating.objects.create(user=customer, product=product, score=5)
    customer.set_password("changed-during-demo")
    customer.save()

    run_reset()

    customer.refresh_from_db()
    assert Order.objects.filter(user=customer).count() == 1
    assert not Rating.objects.filter(user=customer).exists()
    assert customer.check_password("brewnook-demo")
    # Stock comes back from the spreadsheet (42) minus the one delivered order.
    assert Product.objects.get(model="DB-ETH-250").quantity_in_stock == 41


@override_settings(DEBUG=True)
def test_removes_accounts_registered_during_a_demo():
    run_reset()
    signup = User.objects.create_user(email="new@demo.brewnook.dev", password="x")
    keep = User.objects.create_user(email="real@example.com", password="x")

    run_reset()

    assert not User.objects.filter(pk=signup.pk).exists()
    assert User.objects.filter(pk=keep.pk).exists()


@override_settings(DEBUG=False)
def test_refuses_without_yes_when_debug_is_off():
    with pytest.raises(CommandError):
        run_reset()
    assert not User.objects.filter(email="customer@brewnook.dev").exists()