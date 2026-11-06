# backend

Django + Django REST Framework API for Brewnook.

| Path | Purpose |
| --- | --- |
| `config/` | Django project package: URLs, WSGI/ASGI entry points, settings |
| `core/` | Cross-cutting endpoints such as the health check |
| `catalog/` | Products and categories: models, `seed_catalog` command, public catalog API |
| `requirements.txt` | Pinned Python dependencies |
| `.env.example` | Template for `backend/.env` (local values only) |
| `pytest.ini` | pytest configuration (uses `config.settings.dev`) |

## Settings

`manage.py` defaults to `config.settings.dev`. WSGI/ASGI default to
`config.settings.prod`. Override with `DJANGO_SETTINGS_MODULE`.

| Variable | Used by | Description |
| --- | --- | --- |
| `SECRET_KEY` | all | Django secret key |
| `DATABASE_URL` | all | PostgreSQL connection URL |
| `CORS_ALLOWED_ORIGINS` | all | Comma-separated origins (dev defaults to the Vite server on port 5173) |
| `ALLOWED_HOSTS` | prod | Comma-separated host names (required) |

## Tests

```bash
pytest
```

## Health check

`GET /api/health` returns `{"status": "ok", "db": true}` when `SELECT 1`
succeeds against the database, and `"db": false` otherwise.

## Product catalog

### Seed data

```bash
python manage.py seed_catalog
```

Loads 7 categories and 32 products from `catalog/data/Brewnook_Product_List.xlsx`.
Safe to run again: products are matched by their `model` code, so a re-run
updates existing rows instead of creating duplicates. `popularity` is never
overwritten. Use `--file <path>` to load a different spreadsheet.

### Endpoints

All catalog endpoints are public (no login, Req 4) and read-only (`GET` only).

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/products/` | Paginated product list (12 per page) |
| `GET` | `/api/products/<id>/` | One product; `404` if it does not exist |
| `GET` | `/api/categories/` | All categories (not paginated) |

Query parameters for `/api/products/` (can be combined):

| Parameter | Example | Description |
| --- | --- | --- |
| `category` | `?category=3` | Only products in this category id; `400` if not an integer |
| `search` | `?search=kenya` | Case-insensitive match in name **or** description (Req 7) |
| `ordering` | `?ordering=-price` | `price`, `-price`, `popularity`, `-popularity` (`-` = descending); default is by name |
| `page` | `?page=2` | Page number |
| `page_size` | `?page_size=24` | Items per page, max 100 |

Out-of-stock products are **not** filtered out: they still appear in lists and
search results with `"in_stock": false`, and the frontend disables
"Add to cart" (Req 7).

List response:

```json
{
  "count": 32,
  "next": "http://localhost:8000/api/products/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

Product object:

```json
{
  "id": 4,
  "name": "Kenya AA Whole Bean Coffee",
  "model": "DB-KEN-250",
  "serial_number": "LOT-2609-KEN04",
  "description": "Bright acidity; notes of blackcurrant and grapefruit. Limited lot.",
  "quantity_in_stock": 0,
  "in_stock": false,
  "price": "590.00",
  "warranty_status": "No warranty",
  "warranty_months": 0,
  "distributor_name": "Duskberry Roasters (direct, in-house)",
  "distributor_contact": "supply@duskberry.example",
  "category": { "id": 1, "name": "Coffee Beans" },
  "image": "products/db-ken-250.webp",
  "brand": "Duskberry Roasters",
  "origin": "Kenya",
  "roast_date": "2026-09-15",
  "expiry_date": "2027-09-15",
  "weight_capacity": "250 g",
  "popularity": 0
}
```

Notes:

- `price` is a string (decimal) to avoid floating-point rounding.
- `cost` is internal (used for profit/loss, Req 11) and is never returned by
  the public API. If a product has no cost, 50% of the price is used.
- `roast_date`, `expiry_date` and `origin` may be `null` or empty for equipment.
