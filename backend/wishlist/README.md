# wishlist

Customer wishlist (saved products).

- `models.py`: `WishlistItem` (`user`, `product` → `catalog.Product`,
  `created_at`); one row per user and product (unique constraint).
- `serializers.py`, `views.py`, `urls.py`: API under `/api/wishlist`.
- `admin.py`: read-friendly admin list.

## API

All endpoints are customer-only (`IsCustomer`): anonymous → `401`, other
roles → `403`. Each customer sees and changes only their own items.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/wishlist` | Own items, newest first: `[{"product": {"id", "name", "model", "price", "image", "in_stock"}, "created_at"}]` (not paginated). |
| POST | `/api/wishlist` | `{"product_id": 5}`. `201` when added, `200` when already saved (idempotent); `400` for a missing or unknown product. |
| DELETE | `/api/wishlist/{product_id}` | `204`; `404` if the product is not in the caller's wishlist. |

Deleting a product deletes its wishlist rows (`CASCADE`).
