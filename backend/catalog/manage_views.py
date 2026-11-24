"""
KAN-50 + KAN-59 (Req 12): product-manager API for products, categories and stock.

Product manager only. Not logged in -> 401, any other role -> 403.
No trailing slash, like the other manager endpoints (/api/deliveries ...).

GET    /api/manage/products               all products incl. cost (not paginated)
POST   /api/manage/products               add a product
GET    /api/manage/products/{id}
PUT    /api/manage/products/{id}          edit (price + stock are read-only here)
PATCH  /api/manage/products/{id}          edit only the fields sent
DELETE /api/manage/products/{id}          409 if the product was ever ordered
PATCH  /api/manage/products/{id}/stock    {"quantity_in_stock": 40} or {"change": -3}

GET    /api/manage/categories             with product_count
POST   /api/manage/categories
GET / PUT / PATCH /api/manage/categories/{id}
DELETE /api/manage/categories/{id}        409 while it still has products
"""
from django.db import IntegrityError, transaction
from django.db.models import Count, ProtectedError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsProductManager
from catalog.models import Category, Product
from catalog.serializers import (
    MAX_STOCK,
    ManageCategorySerializer,
    ManageProductSerializer,
    StockUpdateSerializer,
)


class ManageProductViewSet(viewsets.ModelViewSet):
    serializer_class = ManageProductSerializer
    permission_classes = [IsProductManager]
    pagination_class = None  # the manager table sorts on the client, so it needs every row
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        return Product.objects.select_related("category").order_by("name", "id")

    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        try:
            product.delete()
        except (ProtectedError, IntegrityError):
            # OrderItem and Delivery point to the product with on_delete=PROTECT:
            # order history and invoices must keep showing what was bought.
            # IntegrityError covers an order placed in the same instant.
            return Response(
                {
                    "detail": "This product has orders, so it cannot be deleted. "
                    "Set its stock to 0 to stop selling it."
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"], url_path="stock")
    def stock(self, request, pk=None):
        self.get_object()  # 404 if the product does not exist
        serializer = StockUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            # Lock the row, same as checkout (KAN-41). A checkout of this
            # product waits until we commit, so neither change is lost and
            # stock can never go below 0 (Req 18).
            product = Product.objects.select_for_update().get(pk=pk)
            if "quantity_in_stock" in data:
                new_stock = data["quantity_in_stock"]
            else:
                new_stock = product.quantity_in_stock + data["change"]

            if new_stock < 0:
                raise ValidationError(
                    {"change": [f"Only {product.quantity_in_stock} in stock; stock cannot go below 0."]}
                )
            if new_stock > MAX_STOCK:
                raise ValidationError({"change": [f"Stock cannot be more than {MAX_STOCK}."]})

            product.quantity_in_stock = new_stock
            product.save(update_fields=["quantity_in_stock", "updated_at"])

        return Response(ManageProductSerializer(product).data)


class ManageCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ManageCategorySerializer
    permission_classes = [IsProductManager]
    pagination_class = None  # only a handful of categories
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        return Category.objects.annotate(product_count=Count("products")).order_by("name")

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        try:
            category.delete()
        except (ProtectedError, IntegrityError):
            # Product.category uses on_delete=PROTECT.
            return Response(
                {
                    "detail": f"This category still has {category.product_count} product(s). "
                    "Move or delete them first."
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)