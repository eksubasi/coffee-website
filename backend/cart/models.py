from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q


class Cart(models.Model):
    """Server-side shopping cart, one per user (KAN-39, Req 4)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user}"

    @property
    def total_price(self):
        return sum((item.total_price for item in self.items.all()), Decimal("0.00"))


class CartItem(models.Model):
    """A product in a cart. Prices are not stored here: the cart always
    shows the current product price; the order freezes it at checkout."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField()

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["cart", "product"], name="cart_item_unique_product"),
            models.CheckConstraint(condition=Q(quantity__gte=1), name="cart_item_quantity_positive"),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product_id} (cart #{self.cart_id})"

    @property
    def total_price(self):
        return self.product.price * self.quantity