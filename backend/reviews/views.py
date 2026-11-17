"""Ratings (KAN-56) and comments (KAN-57) for products, Req 5.

Ratings
  GET /api/products/{id}/my-rating/   -> {"score": 4 | null, "can_rate": true | false}
  PUT /api/products/{id}/my-rating/   body {"score": 1..5}
      201 first rating, 200 when the customer changes their rating,
      403 if they have no delivered order with this product.
  The product's average and number of ratings are on the product itself:
  "average_rating" and "rating_count" in /api/products/ (catalog app).

Comments
  GET  /api/products/{id}/comments/        public, approved comments only (paginated)
  POST /api/products/{id}/comments/        customer, body {"text": "..."}
       201 with status "pending", 403 if the product was not delivered to them
  GET  /api/products/{id}/comments/mine/   customer's own comments with status
  GET  /api/comments/?status=pending       product manager: moderation queue
  PATCH /api/comments/{id}/approve/        product manager
  PATCH /api/comments/{id}/reject/         product manager
"""

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCustomer, IsProductManager
from catalog.models import Product

from .models import Comment, Rating
from .serializers import (
    CommentInputSerializer,
    ModerationCommentSerializer,
    MyCommentSerializer,
    PublicCommentSerializer,
    RatingInputSerializer,
)
from .services import has_received


# --- Ratings (KAN-56) -----------------------------------------------------------


class MyRatingView(APIView):
    permission_classes = [IsCustomer]

    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        rating = Rating.objects.filter(user=request.user, product=product).first()
        return Response(
            {
                "score": rating.score if rating else None,
                "can_rate": has_received(request.user, product),
            }
        )

    def put(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        serializer = RatingInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not has_received(request.user, product):
            return Response(
                {"detail": "You can only rate products that were delivered to you."},
                status=status.HTTP_403_FORBIDDEN,
            )

        score = serializer.validated_data["score"]
        try:
            # Savepoint: if two requests insert at the same moment, the unique
            # constraint stops the second one and we update instead.
            with transaction.atomic():
                rating, created = Rating.objects.update_or_create(
                    user=request.user, product=product, defaults={"score": score}
                )
        except IntegrityError:
            rating = Rating.objects.get(user=request.user, product=product)
            rating.score = score
            rating.save(update_fields=["score", "updated_at"])
            created = False

        return Response(
            {"score": rating.score, "can_rate": True},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# --- Comments (KAN-57) ----------------------------------------------------------


class ProductCommentsView(generics.ListCreateAPIView):
    """Anyone can read approved comments; only customers who received the product can post."""

    serializer_class = PublicCommentSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsCustomer()]

    def get_product(self):
        return get_object_or_404(Product, pk=self.kwargs["product_id"])

    def get_queryset(self):
        return Comment.objects.filter(
            product=self.get_product(), status=Comment.Status.APPROVED
        ).select_related("user")

    def create(self, request, *args, **kwargs):
        product = self.get_product()
        serializer = CommentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not has_received(request.user, product):
            return Response(
                {"detail": "You can only comment on products that were delivered to you."},
                status=status.HTTP_403_FORBIDDEN,
            )
        comment = Comment.objects.create(
            user=request.user, product=product, text=serializer.validated_data["text"]
        )
        return Response(MyCommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class MyProductCommentsView(generics.ListAPIView):
    """The customer's own comments on one product, including pending and rejected ones."""

    permission_classes = [IsCustomer]
    serializer_class = MyCommentSerializer
    pagination_class = None

    def get_queryset(self):
        product = get_object_or_404(Product, pk=self.kwargs["product_id"])
        return Comment.objects.filter(product=product, user=self.request.user)


class ModerationQueueView(generics.ListAPIView):
    """GET /api/comments/[?status=pending|approved|rejected]  (oldest first)"""

    permission_classes = [IsProductManager]
    serializer_class = ModerationCommentSerializer

    def get_queryset(self):
        queryset = Comment.objects.select_related("product", "user", "reviewed_by").order_by(
            "created_at", "id"
        )
        wanted = self.request.query_params.get("status")
        if wanted is not None:
            if wanted not in Comment.Status.values:
                raise ValidationError({"status": "Use pending, approved or rejected."})
            queryset = queryset.filter(status=wanted)
        return queryset


class _ReviewCommentView(APIView):
    permission_classes = [IsProductManager]
    new_status = None

    def patch(self, request, pk):
        # A manager may also change their mind (e.g. approve a rejected comment).
        with transaction.atomic():
            comment = get_object_or_404(Comment.objects.select_for_update(), pk=pk)
            comment.status = self.new_status
            comment.reviewed_by = request.user
            comment.reviewed_at = timezone.now()
            comment.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        comment = Comment.objects.select_related("product", "user", "reviewed_by").get(pk=pk)
        return Response(ModerationCommentSerializer(comment).data)


class ApproveCommentView(_ReviewCommentView):
    new_status = Comment.Status.APPROVED


class RejectCommentView(_ReviewCommentView):
    new_status = Comment.Status.REJECTED