"""KAN-65: a customer cancels their own order while it is still processing."""

import threading
from decimal import Decimal

import pytest
from django.db import connection
from rest_framework.test import APIClient

from accounts.models import User
from catalog.models import Product
from orders.models import Delivery, Order, OrderItem
from orders.services import StatusChangeError, cancel_order


@pytest.fixture
def customer_client(customer):
    client = APIClient()
    client.force_authenticate(user=customer)
    return client


def stock(product):
    product.refresh_from_db()
    return product.quantity_in_stock


def test_cancel_processing_order_restores_stock(customer_client, order, products):
    # The order fixture holds 2 x P1 and 1 x P2; both products start with stock 10.
    response = customer_client.post(f"/api/orders/{order.id}/cancel")

    assert response.status_code == 200
    assert response.data["status"] == "cancelled"
    assert stock(products[0]) == 12
    assert stock(products[1]) == 11
    order.refresh_from_db()
    assert order.status == Order.Status.CANCELLED


def test_cancel_takes_back_popularity(customer_client, order, products):
    Product.objects.filter(pk=products[0].pk).update(popularity=5)

    customer_client.post(f"/api/orders/{order.id}/cancel")

    products[0].refresh_from_db()
    products[1].refresh_from_db()
    assert products[0].popularity == 3
    assert products[1].popularity == 0  # was 0, does not go negative


@pytest.mark.parametrize(
    "current", [Order.Status.IN_TRANSIT, Order.Status.DELIVERED, Order.Status.CANCELLED]
)
def test_only_processing_orders_can_be_cancelled(customer_client, order, products, current):
    Order.objects.filter(pk=order.pk).update(status=current)

    response = customer_client.post(f"/api/orders/{order.id}/cancel")

    assert response.status_code == 409
    assert stock(products[0]) == 10
    order.refresh_from_db()
    assert order.status == current


def test_cancelling_twice_restores_stock_once(customer_client, order, products):
    first = customer_client.post(f"/api/orders/{order.id}/cancel")
    second = customer_client.post(f"/api/orders/{order.id}/cancel")

    assert first.status_code == 200
    assert second.status_code == 409
    assert stock(products[0]) == 12


def test_cannot_cancel_someone_elses_order(order, products):
    other = User.objects.create_user(email="other@orders.test", password="x")
    client = APIClient()
    client.force_authenticate(user=other)

    response = client.post(f"/api/orders/{order.id}/cancel")

    assert response.status_code == 404
    order.refresh_from_db()
    assert order.status == Order.Status.PROCESSING
    assert stock(products[0]) == 10


def test_unknown_order_is_404(customer_client, db):
    assert customer_client.post("/api/orders/999999/cancel").status_code == 404


def test_cancel_requires_login(order):
    response = APIClient().post(f"/api/orders/{order.id}/cancel")
    assert response.status_code == 401


def test_staff_cannot_use_customer_cancel(order, pm):
    assert pm.post(f"/api/orders/{order.id}/cancel").status_code == 403


def test_cancelled_order_items_leave_the_delivery_list(customer_client, order, pm):
    assert len(pm.get("/api/deliveries").data["results"]) == 2

    customer_client.post(f"/api/orders/{order.id}/cancel")

    assert pm.get("/api/deliveries").data["results"] == []
    # The records are kept (for history), only hidden from the to-do list.
    assert Delivery.objects.filter(order_item__order=order).count() == 2


def test_cancelled_order_cannot_be_shipped_afterwards(customer_client, order, pm):
    customer_client.post(f"/api/orders/{order.id}/cancel")

    response = pm.patch(f"/api/orders/{order.id}/status", {"status": "in-transit"}, format="json")

    assert response.status_code == 409


def test_service_raises_for_other_users_order(order):
    other = User.objects.create_user(email="other2@orders.test", password="x")
    with pytest.raises(Order.DoesNotExist):
        cancel_order(order.id, other)


@pytest.mark.django_db(transaction=True)
def test_two_simultaneous_cancels_restore_stock_once(customer, products):
    """Double-clicked Cancel button: two requests at the same time."""
    order = Order.objects.create(user=customer, address="1 Coffee Street")
    OrderItem.objects.create(order=order, product=products[0], quantity=3, unit_price=Decimal("100.00"))

    results = []
    barrier = threading.Barrier(2)

    def cancel():
        barrier.wait()
        try:
            cancel_order(order.id, customer)
            results.append("ok")
        except StatusChangeError:
            results.append("conflict")
        finally:
            connection.close()

    threads = [threading.Thread(target=cancel) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == ["conflict", "ok"]
    assert stock(products[0]) == 13