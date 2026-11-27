# Progress demo — click-path script (KAN-71)

Shows Req 1, 3, 4, 5, 7 and 9 in under 15 minutes.

## Before the demo (2 min)

```bash
docker compose up -d --wait
cd backend
python manage.py demo_reset          # on the deployed database: python manage.py demo_reset --yes
python manage.py runserver
# second terminal
cd frontend && npm run dev           # http://localhost:5173
```

`demo_reset` reseeds the catalog, resets the four demo accounts (password `brewnook-demo`),
deletes accounts registered during earlier demos (`@demo.brewnook.dev`) and creates one
delivered order (Ethiopia Yirgacheffe) for the demo customer.

| Role | Email |
|------|-------|
| Customer | `customer@brewnook.dev` |
| Product manager | `product@brewnook.dev` |
| Sales manager | `sales@brewnook.dev` |
| Support agent | `support@brewnook.dev` |

Use a private window so the guest cart starts empty.

## Script

| # | Min | Req | Click path | What to point out |
|---|-----|-----|------------|-------------------|
| 1 | 1.5 | 1 | Home → **Coffee Beans** category → product cards | Products grouped by category; price and stock on every card |
| 2 | 1.5 | 9 | Open **Brazil Cerrado** | Name, model, serial/lot, description, stock quantity, price, warranty, distributor; coffee: origin, roast date |
| 3 | 1.5 | 7 | Search `kenya` → then a word from a description (e.g. `chocolate`) → sort price ↑ / ↓ → most popular | Name **and** description search; Kenya AA is out of stock but still listed; "Add to cart" disabled |
| 4 | 2 | 4 | As a guest add 2 products → Cart → change a quantity → **Log in to check out** → register `newcustomer@demo.brewnook.dev` | Browsing and cart need no login; checkout does; cart is kept after registering |
| 5 | 3 | 3 | **Proceed to checkout** → card `4111 1111 1111 1111`, `12/30`, `123` → **Pay** | Order confirmation, invoice on screen + **Download PDF**, invoice email (backend terminal), order in **Orders** with status *Processing* |
| 6 | 2 | 5 | Log out → log in as `customer@brewnook.dev` → **Orders** → delivered Ethiopia order → product page → rate + comment | Only delivered products can be rated/commented; rating shows immediately, comment waits for approval |
| 7 | 1.5 | 5 | Log in as `product@brewnook.dev` → **Manage → Comments** → approve the comment → product page | Comment visible only after product-manager approval |

Total ≈ 13 min. Reset with `demo_reset` before every rehearsal.

## Rehearsal log

| Date | Duration | Result | Notes |
|------|----------|--------|-------|
| | | | |