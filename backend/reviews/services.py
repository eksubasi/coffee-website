"""Who may rate (and later comment on) a product (KAN-56, Req 5)."""

from orders.models import Order, OrderItem


def has_received(user, product):
    """True if the user has a delivered order that contains this product.

    Cancelled or refunded orders do not count, nor do orders still on the way.
    """
    return OrderItem.objects.filter(
        order__user=user,
        order__status=Order.Status.DELIVERED,
        product=product,
    ).exists()