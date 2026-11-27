from rest_framework import serializers

from catalog.models import Product

from .models import WishlistItem


class WishlistProductSerializer(serializers.ModelSerializer):
    """Short product summary for wishlist cards."""

    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "model", "price", "image", "in_stock"]
        read_only_fields = fields


class WishlistItemSerializer(serializers.ModelSerializer):
    product = WishlistProductSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["product", "created_at"]
        read_only_fields = fields


class WishlistAddSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product"
    )
