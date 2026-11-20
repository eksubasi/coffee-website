import uuid

from django.db import models
from django.utils import timezone


def invoice_number():
    return f"BN-{uuid.uuid4().hex.upper()}"


class Invoice(models.Model):
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="invoice",
    )
    number = models.CharField(
        max_length=40,
        unique=True,
        default=invoice_number,
        editable=False,
    )
    issued_at = models.DateTimeField(default=timezone.now, editable=False)

    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    tax_id = models.CharField(max_length=11, blank=True)
    billing_address = models.TextField()

    line_items = models.JSONField()
    total = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="TRY")

    class Meta:
        ordering = ["-issued_at", "-id"]

    def __str__(self):
        return self.number