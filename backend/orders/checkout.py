"""Checkout: turn the customer's cart into an order (KAN-41, Req 3 + Req 18).

Everything happens in one database transaction. The product rows are locked
with SELECT ... FOR UPDATE, so when two customers buy the last item at the
same time, the second one waits for the first, then sees the new stock and
fails. If any item does not have enough stock, nothing is changed.
"""

from django.db import transaction
from django.db.models import F

from cart.models import Cart
from catalog.models import Product

from .models import Order, OrderItem


class CheckoutError(Exception):
    def __init__(self, message, problems=None):
        super().__init__(message)
        self.message = message
        self.problems = problems or []


@transaction.atomic
def checkout(user, address, payment_token):
    # Lock the cart first: a double-clicked "Buy" button cannot create two orders.
    cart = Cart.objects.select_for_update().filter(user=user).first()
    items = list(cart.items.all()) if cart else []
    if not items:
        raise CheckoutError("Your cart is empty.")

    # Lock the products, always in id order so two checkouts cannot deadlock.
    products = {
        product.id: product
        for product in Product.objects.select_for_update()
        .filter(id__in=[item.product_id for item in items])
        .order_by("id")
    }

    problems = [
        {
            "product": item.product_id,
            "product_name": products[item.product_id].name,
            "requested": item.quantity,
            "available": products[item.product_id].quantity_in_stock,
        }
        for item in items
        if item.quantity > products[item.product_id].quantity_in_stock
    ]
    if problems:
        raise CheckoutError("Not enough stock for some items.", problems)

    order = Order.objects.create(user=user, address=address, payment_token=payment_token)
    for item in items:
        product = products[item.product_id]
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item.quantity,
            # Discounts do not exist yet (sales manager, later sprint): full price.
            unit_price=product.price,
        )
        Product.objects.filter(pk=product.pk).update(
            quantity_in_stock=F("quantity_in_stock") - item.quantity,
            popularity=F("popularity") + item.quantity,
        )

    cart.items.all().delete()
    return order