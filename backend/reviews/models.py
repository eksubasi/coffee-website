"""Product ratings (KAN-56, Req 5). Comments arrive in KAN-57."""

from django.conf import settings
from django.db import models
from django.db.models import Q


class Rating(models.Model):
    """One 1-5 star rating per customer per product.

    Only customers who received the product may rate it (see services.py).
    Ratings are published immediately; only comments need manager approval.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings"
    )
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="ratings"
    )
    score = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="one_rating_per_user_product"),
            models.CheckConstraint(
                condition=Q(score__gte=1) & Q(score__lte=5), name="rating_score_1_to_5"
            ),
        ]

    def __str__(self):
        return f"{self.score}/5 for product {self.product_id} by user {self.user_id}"