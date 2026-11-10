from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCustomer

from . import services
from .models import Cart
from .serializers import CartInputSerializer, CartSerializer


def cart_response(cart):
    """Reload the cart with its products and return it as JSON."""
    cart = Cart.objects.prefetch_related("items__product").get(pk=cart.pk)
    return Response(CartSerializer(cart).data)


class CartView(APIView):
    """GET    /api/cart  -> the user's cart
    PUT    /api/cart  -> replace the cart with the given items
    DELETE /api/cart  -> empty the cart
    """

    permission_classes = [IsCustomer]

    def get(self, request):
        return cart_response(services.get_cart(request.user))

    def put(self, request):
        serializer = CartInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = services.get_cart(request.user)
        services.set_items(cart, serializer.validated_data["items"], add_to_existing=False)
        return cart_response(cart)

    def delete(self, request):
        services.clear(services.get_cart(request.user))
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartMergeView(APIView):
    """POST /api/cart/merge  -> add the guest cart (from the browser) after login"""

    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = CartInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = services.get_cart(request.user)
        services.set_items(cart, serializer.validated_data["items"], add_to_existing=True)
        return cart_response(cart)