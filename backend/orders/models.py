from django.conf import settings
from django.db import models
from django.db.models import Q


class Order(models.Model):
    # TODO(KAN-40): minimal Order for deliveries (KAN-45). Checkout, totals,
    # payment reference, invoice and cancellation/stock restore belong to
    # KAN-40 and should extend this model rather than replace it.

    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        IN_TRANSIT = "in-transit", "In transit"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROCESSING
    )
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"


class OrderItem(models.Model):
    # TODO(KAN-40): add any checkout-specific fields (e.g. discount applied).
    # unit_price is the purchase-time price and must not follow later price
    # changes (invoices and refunds use it).

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=1), name="order_item_quantity_positive"
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0), name="order_item_unit_price_non_negative"
            ),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product_id} (order #{self.order_id})"

    @property
    def total_price(self):
        return self.unit_price * self.quantity


class Delivery(models.Model):
    """One delivery record per order item, handled by product managers.

    Created automatically when an OrderItem is created (see signals.py).
    Customer, product, quantity, price and address are copied so the record
    stays readable even if the order is edited later.
    """

    order_item = models.OneToOneField(
        OrderItem, on_delete=models.CASCADE, related_name="delivery"
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="deliveries"
    )
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="deliveries"
    )
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_address = models.TextField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_completed", "created_at", "id"]
        verbose_name_plural = "deliveries"

    def __str__(self):
        return f"Delivery #{self.pk} for order item #{self.order_item_id}"
