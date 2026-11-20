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

## Retrospective

Date: …  ·  Participants: …

### What went well
- …

### What to improve
- …

### Action items (→ Sprint 2 Jira tickets)
| Action | Owner | Jira |
|--------|-------|------|
| … | … | KAN-… |