"""KAN-40: order snapshot fields and the customer's own order endpoints."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.test import APIClient

from accounts.models import User
from orders.models import Order, OrderItem


@pytest.fixture
def customer_client(customer):
    client = APIClient()
    client.force_authenticate(user=customer)
    return client


# --- Model -----------------------------------------------------------------


def test_order_total_is_sum_of_item_totals(order):
    # 2 x 100.00 + 1 x 250.50
    assert order.total_price == Decimal("450.50")


def test_price_snapshot_does_not_follow_product_price_change(order, products):
    products[0].price = Decimal("999.00")
    products[0].save()

    item = order.items.get(product=products[0])
    assert item.unit_price == Decimal("100.00")
    assert order.total_price == Decimal("450.50")


def test_order_item_price_snapshot_cannot_be_changed(order):
    item = order.items.first()
    item.unit_price = Decimal("1.00")

    with pytest.raises(ValidationError):
        item.save()

    item.refresh_from_db()
    assert item.unit_price != Decimal("1.00")


def test_discount_rate_must_be_between_0_and_1(order, products):
    with pytest.raises(IntegrityError):
        OrderItem.objects.create(
            order=order,
            product=products[0],
            quantity=1,
            unit_price=Decimal("50.00"),
            discount_rate=Decimal("1.5"),
        )


# --- API -------------------------------------------------------------------


def test_customer_sees_only_own_orders(customer_client, order, products):
    other = User.objects.create_user(email="other@orders.test", password="x")
    Order.objects.create(user=other, address="Somewhere else")

    response = customer_client.get("/api/orders")

    assert response.status_code == 200
    assert [o["id"] for o in response.data["results"]] == [order.id]


def test_order_detail_shows_items_and_snapshot_prices(customer_client, order):
    response = customer_client.get(f"/api/orders/{order.id}")

    assert response.status_code == 200
    assert response.data["status"] == "processing"
    assert Decimal(response.data["total_price"]) == Decimal("450.50")
    first = response.data["items"][0]
    assert set(first) >= {"product_name", "quantity", "unit_price", "discount_rate", "total_price"}


def test_other_customers_order_returns_404(customer_client):
    other = User.objects.create_user(email="other@orders.test", password="x")
    foreign = Order.objects.create(user=other, address="Somewhere else")

    response = customer_client.get(f"/api/orders/{foreign.id}")

    assert response.status_code == 404


def test_order_endpoints_require_login(db):
    assert APIClient().get("/api/orders").status_code == 401


def test_order_endpoints_are_customer_only(db, pm):
    assert pm.get("/api/orders").status_code == 403