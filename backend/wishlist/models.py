from django.conf import settings
from django.db import models

from catalog.models import Product


class WishlistItem(models.Model):
    """A product a customer saved for later. One row per (user, product)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"], name="wishlist_unique_user_product"
            ),
        ]

    def __str__(self):
        return f"{self.user} -> {self.product}"
