from decimal import Decimal

from django.db import transaction

from orders.models import Order

from .models import Invoice


@transaction.atomic
def create_invoice(order):
    # Concurrent calls for the same order are serialized.
    locked_order = (
        Order.objects.select_for_update()
        .select_related("user")
        .get(pk=order.pk)
    )

    existing = Invoice.objects.filter(order=locked_order).first()
    if existing is not None:
        return existing

    if locked_order.payment_token_id is None:
        raise ValueError("An invoice requires a paid checkout order.")

    items = list(
        locked_order.items.select_related("product").order_by("id")
    )
    if not items:
        raise ValueError("An invoice requires at least one order item.")

    lines = [
        {
            "product_id": item.product_id,
            "name": item.product.name,
            "model": item.product.model,
            "quantity": item.quantity,
            "unit_price": str(item.unit_price),
            "discount_rate": str(item.discount_rate),
            "line_total": str(item.total_price),
        }
        for item in items
    ]

    total = sum(
        (item.total_price for item in items),
        Decimal("0.00"),
    )

    return Invoice.objects.create(
        order=locked_order,
        customer_name=locked_order.user.full_name,
        customer_email=locked_order.user.email,
        tax_id=locked_order.user.tax_id,
        billing_address=locked_order.address,
        line_items=lines,
        total=total,
    )