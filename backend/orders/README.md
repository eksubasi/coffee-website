# orders

Orders, order items and deliveries.

> `Order` and `OrderItem` are a **minimal version** created for KAN-45
> because KAN-40 (checkout/orders) was not available yet. KAN-40 should
> extend them (see the `TODO(KAN-40)` comments in `models.py`).

- `models.py`: `Order` (status `processing` / `in-transit` / `delivered` /
  `cancelled`, address), `OrderItem` (product, quantity, purchase-time
  `unit_price`), `Delivery` (one per order item).
- `signals.py`: creates a `Delivery` whenever an `OrderItem` is created.
- `services.py`: status rules. Completing the last open delivery marks the
  order `delivered`; marking an order `delivered` completes its deliveries.

## Endpoints (product managers only)

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/deliveries[?is_completed=true\|false]` | Paginated delivery list |
| PATCH | `/api/deliveries/{id}/complete` | Mark delivered (idempotent; 409 if the order is cancelled) |
| PATCH | `/api/orders/{id}/status` | Body `{"status": ...}`; allowed: `processing → in-transit → delivered`, `processing → delivered`. Other changes return 409. |

Cancelling an order (and restoring stock) is a customer flow and is not
available through these endpoints.
