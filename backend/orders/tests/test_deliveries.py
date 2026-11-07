from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from orders.models import Delivery, Order, OrderItem
from orders.services import StatusChangeError, change_order_status, complete_delivery

pytestmark = pytest.mark.django_db

NON_PM_ROLES = [User.Role.CUSTOMER, User.Role.SALES_MANAGER, User.Role.SUPPORT_AGENT]


# --- automatic creation -----------------------------------------------------


def test_delivery_is_created_for_each_order_item(order, customer, products):
    deliveries = Delivery.objects.filter(order_item__order=order).order_by("id")

    assert deliveries.count() == 2
    first = deliveries[0]
    assert first.customer == customer
    assert first.product == products[0]
    assert first.quantity == 2
    assert first.total_price == Decimal("200.00")
    assert first.delivery_address == order.address
    assert first.is_completed is False


def test_updating_order_item_does_not_create_another_delivery(order):
    item = order.items.first()
    item.quantity = 3
    item.save()

    assert Delivery.objects.filter(order_item=item).count() == 1


# --- list --------------------------------------------------------------------


def test_product_manager_lists_deliveries(pm, order):
    response = pm.get(reverse("delivery-list"))

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    row = body["results"][0]
    assert row["order_id"] == order.id
    assert row["customer_email"] == order.user.email
    assert {"product_name", "quantity", "total_price", "delivery_address", "is_completed"} <= row.keys()


def test_list_can_filter_by_completion(pm, order):
    complete_delivery(order.items.first().delivery.id)

    open_rows = pm.get(reverse("delivery-list"), {"is_completed": "false"}).json()
    done_rows = pm.get(reverse("delivery-list"), {"is_completed": "true"}).json()

    assert open_rows["count"] == 1
    assert done_rows["count"] == 1
    assert pm.get(reverse("delivery-list"), {"is_completed": "maybe"}).status_code == 400


@pytest.mark.parametrize("role", NON_PM_ROLES)
def test_other_roles_cannot_use_delivery_endpoints(api_as, role, order):
    client = api_as(role)
    delivery_id = order.items.first().delivery.id

    assert client.get(reverse("delivery-list")).status_code == 403
    assert client.patch(reverse("delivery-complete", args=[delivery_id])).status_code == 403
    assert (
        client.patch(reverse("order-status", args=[order.id]), {"status": "in-transit"}, format="json").status_code
        == 403
    )


def test_anonymous_cannot_use_delivery_endpoints(order):
    client = APIClient()

    assert client.get(reverse("delivery-list")).status_code == 401
    assert client.patch(reverse("order-status", args=[order.id]), {"status": "in-transit"}, format="json").status_code == 401


# --- complete ----------------------------------------------------------------


def test_completing_one_of_two_deliveries_keeps_order_open(pm, order):
    delivery = order.items.first().delivery

    response = pm.patch(reverse("delivery-complete", args=[delivery.id]))

    assert response.status_code == 200
    assert response.json()["is_completed"] is True
    assert response.json()["completed_at"]
    order.refresh_from_db()
    assert order.status == Order.Status.PROCESSING


def test_completing_all_deliveries_marks_order_delivered(pm, order):
    order.status = Order.Status.IN_TRANSIT
    order.save()

    for item in order.items.all():
        assert pm.patch(reverse("delivery-complete", args=[item.delivery.id])).status_code == 200

    order.refresh_from_db()
    assert order.status == Order.Status.DELIVERED


def test_completing_is_idempotent(pm, order):
    delivery = order.items.first().delivery
    first = pm.patch(reverse("delivery-complete", args=[delivery.id])).json()
    second = pm.patch(reverse("delivery-complete", args=[delivery.id])).json()

    assert first["completed_at"] == second["completed_at"]


def test_cannot_complete_delivery_of_cancelled_order(pm, order):
    Order.objects.filter(pk=order.pk).update(status=Order.Status.CANCELLED)
    delivery = order.items.first().delivery

    response = pm.patch(reverse("delivery-complete", args=[delivery.id]))

    assert response.status_code == 409
    delivery.refresh_from_db()
    assert delivery.is_completed is False


def test_complete_unknown_delivery_returns_404(pm):
    assert pm.patch(reverse("delivery-complete", args=[999999])).status_code == 404


# --- order status ------------------------------------------------------------


@pytest.mark.parametrize(
    "start,new,expected",
    [
        (Order.Status.PROCESSING, "in-transit", 200),
        (Order.Status.IN_TRANSIT, "delivered", 200),
        (Order.Status.PROCESSING, "delivered", 200),
        (Order.Status.IN_TRANSIT, "processing", 409),
        (Order.Status.DELIVERED, "in-transit", 409),
        (Order.Status.CANCELLED, "in-transit", 409),
        (Order.Status.PROCESSING, "cancelled", 409),  # cancellation is KAN-40's flow
    ],
)
def test_order_status_transitions(pm, order, start, new, expected):
    Order.objects.filter(pk=order.pk).update(status=start)

    response = pm.patch(reverse("order-status", args=[order.id]), {"status": new}, format="json")

    assert response.status_code == expected
    order.refresh_from_db()
    assert order.status == (new if expected == 200 else start)


def test_setting_status_to_same_value_is_a_no_op(pm, order):
    response = pm.patch(reverse("order-status", args=[order.id]), {"status": "processing"}, format="json")

    assert response.status_code == 200


def test_unknown_status_value_is_rejected(pm, order):
    response = pm.patch(reverse("order-status", args=[order.id]), {"status": "lost"}, format="json")

    assert response.status_code == 400


def test_marking_order_delivered_completes_its_deliveries(pm, order):
    pm.patch(reverse("order-status", args=[order.id]), {"status": "delivered"}, format="json")

    assert not Delivery.objects.filter(order_item__order=order, is_completed=False).exists()


def test_order_status_unknown_order_returns_404(pm):
    response = pm.patch(reverse("order-status", args=[999999]), {"status": "in-transit"}, format="json")

    assert response.status_code == 404


# --- service layer -----------------------------------------------------------


def test_service_rejects_backwards_transition(order):
    change_order_status(order.id, Order.Status.IN_TRANSIT)

    with pytest.raises(StatusChangeError):
        change_order_status(order.id, Order.Status.PROCESSING)


def test_order_item_total_price(products, customer):
    order = Order.objects.create(user=customer, address="x")
    item = OrderItem.objects.create(order=order, product=products[1], quantity=3, unit_price=Decimal("250.50"))

    assert item.total_price == Decimal("751.50")
    assert item.delivery.total_price == Decimal("751.50")
