"""Product ratings (KAN-56) and comments (KAN-57), Req 5."""

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


class Comment(models.Model):
    """A customer's written comment on a product they received (KAN-57).

    New comments are "pending" and invisible to other visitors until a
    product manager approves them (Req 5).
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # Who approved or rejected it, and when (empty while pending).
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_comments",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Comment #{self.pk} on product {self.product_id} ({self.status})"