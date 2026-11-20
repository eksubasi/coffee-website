# Sprint 2 — Review demo script & results

## Review demo (≈10 min)

**Setup:** `docker compose up -d --wait` → backend `python manage.py runserver` → frontend `npm run dev` → http://localhost:5173 in a private window. Invoice emails print to the backend terminal (console email backend).

| # | Step | What to show |
|---|------|--------------|
| 1 | Add 2 products to the cart as a guest | Cart works without login, "Log in to check out" |
| 2 | Register a new customer | Name, email, tax ID, address; form validation |
| 3 | Open the cart after registering | Guest cart is kept |
| 4 | Checkout with mock card `4111 1111 1111 1111`, `12/30`, `123` | Address prefilled, total matches cart |
| 5 | Confirmation page | Invoice on screen + Download PDF; email in backend terminal |
| 6 | Orders → order detail | Status "Processing", items, total, invoice |
| 7 | Log in as `product@brewnook.dev` → Manage → Deliveries | Mark the order delivered |

## Rehearsal results

Date: 20 Nov 2026 · Environment: local (Docker Postgres 16 + Redis, Django, Vite) · Tested by: Ahmet Efe

| # | Step | Result |
|---|------|--------|
| 1 | Guest cart | ✅ Pass |
| 2 | Register | ✅ Pass |
| 3 | Cart kept after login | ✅ Pass |
| 4 | Checkout with mock card | ✅ Pass |
| 5 | Invoice on screen + PDF + email | ⚠️ Pass with bug: invoice number on screen differs from PDF/email (filed in KAN-54) |
| 6 | Order history and detail | ✅ Pass |
| 7 | Product manager marks delivered | ❌ Blocked: Deliveries page not built yet (planned in KAN-60). Backend works: `PATCH /api/orders/<id>/status` |

6 of 7 steps work. Step 7 needs KAN-60 before the review.