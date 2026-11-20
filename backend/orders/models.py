from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

class Order(models.Model):
    

    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        IN_TRANSIT = "in-transit", "In transit"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROCESSING
    )
    address = models.TextField()
    # Card used to pay (KAN-41). Empty only for orders created before checkout existed.
    payment_token = models.ForeignKey(
        "payments.PaymentToken",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"

    @property
    def total_price(self):
        """Sum of the item totals. Items cannot change, so neither can this."""
        return sum((item.total_price for item in self.items.all()), Decimal("0.00"))


class OrderItem(models.Model):

    PRICE_SNAPSHOT_FIELDS = ("unit_price", "discount_rate")


    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    discount_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal("0"))


    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=1), name="order_item_quantity_positive"
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0), name="order_item_unit_price_non_negative"
            ),
            models.CheckConstraint(
                condition=Q(discount_rate__gte=0) & Q(discount_rate__lte=1),
                name="order_item_discount_rate_between_0_and_1",
            ),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product_id} (order #{self.order_id})"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            saved = (
                OrderItem.objects.filter(pk=self.pk)
                .values(*self.PRICE_SNAPSHOT_FIELDS)
                .first()
            )
            if saved is not None:
                changed = [
                    field
                    for field in self.PRICE_SNAPSHOT_FIELDS
                    if getattr(self, field) != saved[field]
                ]
                if changed:
                    raise ValidationError(
                        f"Purchase-time prices cannot be changed: {', '.join(changed)}."
                    )
        super().save(*args, **kwargs)
    

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
