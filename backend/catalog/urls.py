from rest_framework.routers import DefaultRouter, SimpleRouter

from catalog.manage_views import ManageCategoryViewSet, ManageProductViewSet
from catalog.views import CategoryViewSet, ProductViewSet

# The router creates the list (/products/) and detail (/products/<id>/) URLs
router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("categories", CategoryViewSet, basename="category")

# KAN-50 / KAN-59: product-manager endpoints. No trailing slash, like the other
# manager endpoints (/api/deliveries, /api/orders/{id}/status), so a POST
# without "/" cannot hit the APPEND_SLASH error from KAN-121.
manage_router = SimpleRouter(trailing_slash=False)
manage_router.register("manage/products", ManageProductViewSet, basename="manage-product")
manage_router.register("manage/categories", ManageCategoryViewSet, basename="manage-category")

urlpatterns = router.urls + manage_router.urls