from django.urls import path

from . import views

urlpatterns = [
    # Ratings (KAN-56)
    path(
        "products/<int:product_id>/my-rating/",
        views.MyRatingView.as_view(),
        name="product-my-rating",
    ),
    # Comments (KAN-57)
    path(
        "products/<int:product_id>/comments/",
        views.ProductCommentsView.as_view(),
        name="product-comments",
    ),
    path(
        "products/<int:product_id>/comments/mine/",
        views.MyProductCommentsView.as_view(),
        name="product-my-comments",
    ),
    path("comments/", views.ModerationQueueView.as_view(), name="comment-moderation"),
    path("comments/<int:pk>/approve/", views.ApproveCommentView.as_view(), name="comment-approve"),
    path("comments/<int:pk>/reject/", views.RejectCommentView.as_view(), name="comment-reject"),
]