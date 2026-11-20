from rest_framework import serializers

from catalog.models import Product

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    unit_price = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2, read_only=True
    )
    stock = serializers.IntegerField(source="product.quantity_in_stock", read_only=True)
    image = serializers.CharField(source="product.image", read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "product",
            "product_name",
            "unit_price",
            "quantity",
            "stock",
            "image",
            "total_price",
        ]
        read_only_fields = fields


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ["items", "total_price", "updated_at"]
        read_only_fields = fields


class CartItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=0)


class CartInputSerializer(serializers.Serializer):
    """Body of PUT /api/cart and POST /api/cart/merge:
    {"items": [{"product": 5, "quantity": 2}, ...]}"""

    items = CartItemInputSerializer(many=True)