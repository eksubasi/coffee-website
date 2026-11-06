"""
Catalog models for Brewnook (KAN-22).

Req 9: every product has at least id, name, model, serial number, description,
quantity in stock, price, warranty status and distributor information.
Req 11: cost may be left empty -> it defaults to 50% of the sale price.
Req 7: products can be sorted by popularity, so we keep a counter.
"""
from decimal import Decimal

from django.db import models
from django.db.models import Q


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    class WarrantyStatus(models.TextChoices):
        NO_WARRANTY = "No warranty", "No warranty"
        UNDER_WARRANTY = "Under warranty", "Under warranty"

    #       Req 9 core fields
    # "id" is created automatically by Django (auto-increment primary key).
    name = models.CharField(max_length=200)
    # Model code is unique: the seed command upserts products by this value.
    model = models.CharField(max_length=100, unique=True)
    # SN-... for equipment, LOT-... for coffee
    serial_number = models.CharField(max_length=100)
    description = models.TextField()
    quantity_in_stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Nullable on purpose: empty cost -> 50% of price (see effective_cost)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    warranty_status = models.CharField(
        max_length=20, choices=WarrantyStatus.choices, default=WarrantyStatus.NO_WARRANTY
    )
    warranty_months = models.PositiveSmallIntegerField(default=0)
    distributor_name = models.CharField(max_length=200)
    distributor_contact = models.CharField(max_length=200, blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,  # a category with products cannot be deleted by accident
        related_name="products",
    )
    # Path to the image file (e.g. "images/kenya-aa.jpg"), not an upload field
    image = models.CharField(max_length=255, blank=True)

    #  Optional coffee-specific fields 
    brand = models.CharField(max_length=100, blank=True)
    origin = models.CharField(max_length=100, blank=True)
    roast_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    # Free text because it varies by category: "250 g", "Hopper: 30 g", "Water tank: 1.5 L"
    weight_capacity = models.CharField(max_length=100, blank=True)

    #  Req 7: sort by popularity 
    popularity = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [ # req 17 example of defensive programming
            models.CheckConstraint(condition=Q(price__gte=0), name="product_price_non_negative"),
            models.CheckConstraint(
                condition=Q(cost__isnull=True) | Q(cost__gte=0),
                name="product_cost_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.model})"

    @property
    def in_stock(self):
        """Out-of-stock products stay visible but cannot go into the cart (Req 7)."""
        return self.quantity_in_stock > 0

    @property
    def effective_cost(self):
        """Cost used for profit/loss (Req 11): given cost, or 50% of price."""
        if self.cost is not None:
            return self.cost
        return (self.price * Decimal("0.5")).quantize(Decimal("0.01"))
