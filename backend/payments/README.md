# payments

Simulated bank for checkout (KAN-42). Payments always succeed once the card
data is valid; no real payment provider is involved.

- `POST /api/payments/mock` (customers only): body `card_number`, `expiry`
  (`MM/YY`), `cvv`, `holder`. Validates the card number with the Luhn
  check, the expiry format and date, and the CVV format. Returns
  `{"status": "approved", "payment_token", "last4"}`.
- `cards.py`: Luhn, expiry parsing, and the card token
  (`sha256(card_number + SECRET_KEY)`).
- `models.py`: `PaymentToken(user, last4, token)`.

**Card data rules:** the full card number (PAN) and the CVV are never
stored, logged or returned. Only `last4` and the token are persisted.
Changing `SECRET_KEY` changes the token for the same card.
