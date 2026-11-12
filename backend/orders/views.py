from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCustomer, IsProductManager

from .models import Delivery, Order
from .serializers import (
    CustomerOrderSerializer,
    DeliverySerializer,
    OrderSerializer,
    OrderStatusSerializer,
    CheckoutSerializer,
)
from .checkout import CheckoutError, checkout
from .services import StatusChangeError, change_order_status, complete_delivery


class DeliveryListView(generics.ListAPIView):
    """GET /api/deliveries[?is_completed=true|false]"""

    permission_classes = [IsProductManager]
    serializer_class = DeliverySerializer

    def get_queryset(self):
        queryset = Delivery.objects.select_related("customer", "product", "order_item")
        flag = self.request.query_params.get("is_completed")
        if flag is not None:
            if flag not in ("true", "false"):
                raise ValidationError({"is_completed": "Use true or false."})
            queryset = queryset.filter(is_completed=(flag == "true"))
        return queryset


class DeliveryCompleteView(APIView):
    """PATCH /api/deliveries/{id}/complete"""

    permission_classes = [IsProductManager]

    def patch(self, request, pk):
        get_object_or_404(Delivery, pk=pk)
        try:
            delivery = complete_delivery(pk)
        except StatusChangeError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        delivery.refresh_from_db()
        return Response(DeliverySerializer(delivery).data)


class OrderStatusView(APIView):
    """PATCH /api/orders/{id}/status  body: {"status": "in-transit" | "delivered"}"""

    permission_classes = [IsProductManager]

    def patch(self, request, pk):
        get_object_or_404(Order, pk=pk)
        serializer = OrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = change_order_status(pk, serializer.validated_data["status"])
        except StatusChangeError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(OrderSerializer(order).data)


class CustomerOrderMixin:
    """Customers only ever see their own orders; others get 404, not 403,
    so order ids of other users are not revealed."""

    permission_classes = [IsCustomer]
    serializer_class = CustomerOrderSerializer

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items__product")
        )


class CustomerOrderListView(CustomerOrderMixin, generics.ListAPIView):
    """GET /api/orders  (own orders, newest first, paginated)"""


class CustomerOrderDetailView(CustomerOrderMixin, generics.RetrieveAPIView):
    """GET /api/orders/{id}"""

class CheckoutView(APIView):
    """POST /api/checkout  -> turns the cart into an order (201), or
    409 with the items that do not have enough stock, or 400 if the cart is empty."""

    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            order = checkout(
                request.user,
                serializer.validated_data["address"],
                serializer.validated_data["payment_token"],
            )
        except CheckoutError as exc:
            code = status.HTTP_409_CONFLICT if exc.problems else status.HTTP_400_BAD_REQUEST
            return Response({"detail": exc.message, "problems": exc.problems}, status=code)
        order = Order.objects.prefetch_related("items__product").get(pk=order.pk)
        return Response(CustomerOrderSerializer(order).data, status=status.HTTP_201_CREATED)