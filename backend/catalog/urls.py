from rest_framework.routers import DefaultRouter

from catalog.views import CategoryViewSet, ProductViewSet

# The router creates the list (/products/) and detail (/products/<id>/) URLs
router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("categories", CategoryViewSet, basename="category")

urlpatterns = router.urls
