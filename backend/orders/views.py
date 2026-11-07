from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsProductManager

from .models import Delivery, Order
from .serializers import DeliverySerializer, OrderSerializer, OrderStatusSerializer
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
