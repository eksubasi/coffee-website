# Sprint 1 — Review demo script & retrospective

## Review demo (≈10 min)

**Setup (before the meeting)**
- `docker compose up -d --wait`
- Backend: `cd backend` → `python manage.py seed_catalog` → `python manage.py runserver`
- Frontend: `cd frontend` → `npm run dev` → open http://localhost:5173
- Use a private/incognito window so the guest cart starts empty.

| # | Min | Step | What to show | Requirement |
|---|-----|------|--------------|-------------|
| 1 | 1 | Home page | Store concept, 7 categories, navbar | — |
| 2 | 2 | Open a category (e.g. Coffee Beans) | Products filtered by category, price & stock badge on each card | Browse by category |
| 3 | 2 | Open a product detail | Name, model, description, price (TRY), stock, warranty, distributor; coffee: origin & roast date | Product details |
| 4 | 1 | Open an out-of-stock product | Still visible, "Add to cart" disabled | Out-of-stock stays visible |
| 5 | 2 | Search: `kenya`, then a word that only appears in a description | Matches name **and** description; out-of-stock items appear in results | Req 7 search |
| 6 | 1 | Sort by price ↑ / ↓ and by popularity | Order changes both directions | Req 7 sort |
| 7 | 1 | Guest cart: add 2 products, change a quantity, remove one | Cart works without login, totals update | Guest cart |
| 8 | (bonus) | Log in as `customer@brewnook.dev` | Guest cart is merged into the user's cart | Cart kept on login |

**Backup plan:** if anything breaks live, show `/api/products/?search=kenya&ordering=-price` in the browser and the test run (`pytest`).

## Demo rehearsal results

Date: 20 Nov 2026 · Environment: local (Docker Postgres 16 + Django + Vite) · Tested by: Ahmet Efe

| # | Step | Result |
|---|------|--------|
| 1 | Home page: categories and navbar | ✅ Pass |
| 2 | Category page: products filtered, price & stock on cards | ✅ Pass |
| 3 | Product detail: description, price, stock, warranty, distributor, origin/roast date | ✅ Pass |
| 4 | Out-of-stock product (Kenya AA, Burrwick E64): visible, "Add to cart" disabled | ✅ Pass |
| 5 | Search `kenya`: matches name/description, out-of-stock item shown | ✅ Pass |
| 6 | Sort by price ↑/↓ and popularity | ✅ Pass |
| 7 | Guest cart: add, change quantity, remove, totals update | ✅ Pass |
| 8 | Login as customer: guest cart kept after login | ✅ Pass |

All 8 demo steps passed. No blocking issues found.