from rest_framework import serializers

from .models import Delivery, Order, OrderItem

class DeliverySerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order_item.order_id", read_only=True)
    customer_email = serializers.EmailField(source="customer.email", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Delivery
        fields = [
            "id",
            "order_id",
            "order_item",
            "customer",
            "customer_email",
            "product",
            "product_name",
            "quantity",
            "total_price",
            "delivery_address",
            "is_completed",
            "completed_at",
        ]
        read_only_fields = fields


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "user", "status", "address", "created_at", "updated_at"]
        read_only_fields = fields

        
class CustomerOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "quantity",
            "unit_price",
            "discount_rate",
            "total_price",
        ]
        read_only_fields = fields


class CustomerOrderSerializer(serializers.ModelSerializer):
    """What a customer sees for their own orders (KAN-40)."""

    items = CustomerOrderItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "status", "address", "total_price", "items", "created_at", "updated_at"]
        read_only_fields = fields
