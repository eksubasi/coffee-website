from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCustomer

from .models import WishlistItem
from .serializers import WishlistAddSerializer, WishlistItemSerializer


class WishlistView(APIView):
    """GET  /api/wishlist  -> the current customer's saved products
    POST /api/wishlist  -> {"product_id": 5}; 201 if added, 200 if already saved
    """

    permission_classes = [IsCustomer]

    def get(self, request):
        items = WishlistItem.objects.filter(user=request.user).select_related("product")
        return Response(WishlistItemSerializer(items, many=True).data)

    def post(self, request):
        serializer = WishlistAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item, created = WishlistItem.objects.get_or_create(
            user=request.user, product=serializer.validated_data["product"]
        )
        return Response(
            WishlistItemSerializer(item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class WishlistItemView(APIView):
    """DELETE /api/wishlist/{product_id}  -> 204; 404 if not in this user's wishlist"""

    permission_classes = [IsCustomer]

    def delete(self, request, product_id):
        item = get_object_or_404(WishlistItem, user=request.user, product_id=product_id)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
