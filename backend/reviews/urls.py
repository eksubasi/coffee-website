from django.urls import path

from . import views

urlpatterns = [
    path(
        "products/<int:product_id>/my-rating/",
        views.MyRatingView.as_view(),
        name="product-my-rating",
    ),
]