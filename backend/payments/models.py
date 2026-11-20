from django.conf import settings
from django.db import models


class PaymentToken(models.Model):
    """Reference to a card used for a (mock) payment.

    Only the last four digits and a salted hash are stored. The full card
    number (PAN) and the CVV are never persisted.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_tokens",
    )
    last4 = models.CharField(max_length=4)
    token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "token"], name="unique_user_card_token"),
        ]

    def __str__(self):
        return f"**** {self.last4}"
