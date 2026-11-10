"""Cart rules (KAN-39).

Quantities are always capped at the product's stock and out-of-stock
products are dropped (Req 7: they can be seen but not bought). Stock is
checked again at checkout (KAN-41), because it can change after this.
"""

from django.db import transaction

from catalog.models import Product

from .models import Cart, CartItem


def get_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def _sum_by_product(items):
    """[{"product": p, "quantity": n}, ...] -> {product_id: total quantity}"""
    totals = {}
    for item in items:
        product_id = item["product"].id
        totals[product_id] = totals.get(product_id, 0) + item["quantity"]
    return totals


@transaction.atomic
def set_items(cart, items, add_to_existing):
    """Write ``items`` into ``cart``.

    add_to_existing=True  -> merge (guest cart on login): quantities are added
                             to what is already in the cart.
    add_to_existing=False -> replace: the cart becomes exactly ``items``.
    """
    wanted = _sum_by_product(items)
    current = {item.product_id: item for item in cart.items.all()}

    if add_to_existing:
        for product_id, item in current.items():
            wanted[product_id] = wanted.get(product_id, 0) + item.quantity
    else:
        cart.items.exclude(product_id__in=wanted).delete()

    stock = dict(
        Product.objects.filter(id__in=wanted).values_list("id", "quantity_in_stock")
    )
    for product_id, quantity in wanted.items():
        quantity = min(quantity, stock.get(product_id, 0))
        item = current.get(product_id)
        if quantity <= 0:
            if item is not None:
                item.delete()
        elif item is None:
            CartItem.objects.create(cart=cart, product_id=product_id, quantity=quantity)
        elif item.quantity != quantity:
            item.quantity = quantity
            item.save(update_fields=["quantity"])

    cart.save(update_fields=["updated_at"])
    return cart


def clear(cart):
    cart.items.all().delete()
    cart.save(update_fields=["updated_at"])