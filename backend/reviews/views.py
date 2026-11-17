"""KAN-56: a customer rates a product they received (Req 5).

GET /api/products/{id}/my-rating/   -> {"score": 4 | null, "can_rate": true | false}
PUT /api/products/{id}/my-rating/   body {"score": 1..5}
    201 first rating, 200 when the customer changes their rating,
    403 if they have no delivered order with this product.

The product's average and number of ratings are on the product itself:
"average_rating" and "rating_count" in /api/products/ (catalog app).
"""

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCustomer
from catalog.models import Product

from .models import Rating
from .serializers import RatingInputSerializer
from .services import has_received


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