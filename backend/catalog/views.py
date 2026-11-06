"""
KAN-24 + KAN-25: public read-only catalog API.

GET /api/products/              paginated list, optional ?category=<id>
GET /api/products/?search=      search in name OR description (KAN-25)
GET /api/products/?ordering=    price | -price | popularity | -popularity (KAN-25)
GET /api/products/<id>/         one product
GET /api/categories/            all categories
"""
from rest_framework import filters, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from catalog.models import Category, Product
from catalog.serializers import CategorySerializer, ProductSerializer


class ProductPagination(PageNumberPagination):
    page_size = 12                      # 12 cards fit a 3x4 or 4x3 grid
    page_size_query_param = "page_size"  # frontend may ask ?page_size=24
    max_page_size = 100                  # but never more than 100 at once


class StableOrderingFilter(filters.OrderingFilter):
    """
    Adds "id" as a tie-breaker. Without it, products with the same price or
    popularity could swap places between pages, so a product might appear
    on page 1 and again on page 2 (or never).
    """

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        return [*ordering, "id"] if ordering else ordering


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only: customers can view products but never change them here."""

    serializer_class = ProductSerializer
    permission_classes = [AllowAny]  # Req 4: browsing does not require login
    pagination_class = ProductPagination

    # KAN-25 (Req 7). Out-of-stock products are NOT filtered out anywhere,
    # so they still show up in search results; the frontend only disables
    # "Add to cart" using the in_stock field.
    filter_backends = [filters.SearchFilter, StableOrderingFilter]
    search_fields = ["name", "description"]  # case-insensitive "contains", name OR description
    ordering_fields = ["price", "popularity"]  # anything else in ?ordering= is ignored
    ordering = ["name"]                        # default when no ?ordering= is given

    def get_queryset(self):
        # select_related loads each product's category in the same SQL query
        # (avoids one extra query per product, the "N+1" problem)
        queryset = Product.objects.select_related("category")

        category_id = self.request.query_params.get("category")
        if category_id is not None:
            if not category_id.isdigit():
                raise ValidationError({"category": "Must be a category id (integer)."})
            queryset = queryset.filter(category_id=int(category_id))
        return queryset


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None  # only 7 categories: return them all at once
