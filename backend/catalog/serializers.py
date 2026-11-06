"""
KAN-24: serializers turn Product/Category objects into JSON for the API.
"""
from rest_framework import serializers

from catalog.models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class CategoryBriefSerializer(serializers.ModelSerializer):
    """Small version nested inside each product (no description needed there)."""

    class Meta:
        model = Category
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategoryBriefSerializer(read_only=True)
    # Computed in the model (Req 7): frontend disables "Add to cart" when False
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        # Public fields only. "cost" is internal business data (used for
        # profit/loss, Req 11) so it is NOT exposed to customers.
        fields = [
            "id", "name", "model", "serial_number", "description",
            "quantity_in_stock", "in_stock", "price",
            "warranty_status", "warranty_months",
            "distributor_name", "distributor_contact",
            "category", "image",
            "brand", "origin", "roast_date", "expiry_date", "weight_capacity",
            "popularity",
        ]
        read_only_fields = fields
