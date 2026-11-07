"""Delivery and order status rules (KAN-45)."""

from django.db import transaction
from django.utils import timezone

from .models import Delivery, Order

# Status changes a product manager may make through the API.
# Cancelling (and restoring stock) is a customer flow owned by KAN-40.
ALLOWED_TRANSITIONS = {
    Order.Status.PROCESSING: {Order.Status.IN_TRANSIT, Order.Status.DELIVERED},
    Order.Status.IN_TRANSIT: {Order.Status.DELIVERED},
    Order.Status.DELIVERED: set(),
    Order.Status.CANCELLED: set(),
}


class StatusChangeError(Exception):
    pass


def _lock_order(order_id):
    return Order.objects.select_for_update().get(pk=order_id)


@transaction.atomic
def complete_delivery(delivery_id):
    """Mark a delivery completed; mark the order delivered when all are done.

    The order row is locked so two deliveries completed at the same time
    cannot both miss the "all completed" condition.
    """
    delivery = Delivery.objects.select_related("order_item").get(pk=delivery_id)
    order = _lock_order(delivery.order_item.order_id)
    if order.status == Order.Status.CANCELLED:
        raise StatusChangeError("Deliveries of a cancelled order cannot be completed.")

    delivery = Delivery.objects.select_for_update().get(pk=delivery_id)
    if not delivery.is_completed:
        delivery.is_completed = True
        delivery.completed_at = timezone.now()
        delivery.save(update_fields=["is_completed", "completed_at"])

    has_open = Delivery.objects.filter(
        order_item__order=order, is_completed=False
    ).exists()
    if not has_open and order.status != Order.Status.DELIVERED:
        order.status = Order.Status.DELIVERED
        order.save(update_fields=["status", "updated_at"])
    return delivery


@transaction.atomic
def change_order_status(order_id, new_status):
    order = _lock_order(order_id)
    if new_status == order.status:
        return order
    if new_status not in ALLOWED_TRANSITIONS[order.status]:
        raise StatusChangeError(
            f"Cannot change order status from '{order.status}' to '{new_status}'."
        )
    order.status = new_status
    order.save(update_fields=["status", "updated_at"])

    if new_status == Order.Status.DELIVERED:
        Delivery.objects.filter(order_item__order=order, is_completed=False).update(
            is_completed=True, completed_at=timezone.now()
        )
    return order
