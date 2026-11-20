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
    # KAN-56 (Req 5): filled in by ProductViewSet.get_queryset with one SQL query.
    # average_rating is null when nobody has rated the product yet.
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()

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
            "popularity", "average_rating", "rating_count",
        ]
        read_only_fields = fields

    def get_average_rating(self, product):
        average = getattr(product, "average_rating", None)
        return round(average, 1) if average is not None else None

    def get_rating_count(self, product):
        return getattr(product, "rating_count", 0)