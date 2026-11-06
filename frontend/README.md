# Brewnook frontend

React 19 + TypeScript + Vite + Tailwind CSS v4 + shadcn/ui-style components + react-router + Zustand.
Tooling versions and the ESLint config match the team repo (`eksubasi/coffee-website`, `frontend/`); `npm run lint` must pass (CI, KAN-21).

## Run

```bash
npm install
cp .env.example .env
npm run dev        # http://localhost:5173
npm run build      # typecheck + production build
```

## Backend

The frontend talks to the team's Django API (`/api/health`, `/api/categories/`, `/api/products/`). There is no mock mode.
In dev, Vite proxies `/api/*` to `VITE_DEV_PROXY_TARGET` (default `http://localhost:8000`).
Run the backend locally: `DATABASE_URL=sqlite:///db.sqlite3`, `python manage.py migrate`, `python manage.py seed_catalog`, `python manage.py runserver`.

## Temporary files (KAN-30 / Yesim's scope)

`src/components/temp-kan30/` and `src/styles/theme-temp-kan30.css` are placeholders so the pages build until KAN-30 lands; replace them then.

## What is implemented (Sprint 1, M3)

- **KAN-19** scaffold, router, layout shell (navbar with cart badge, footer with API health indicator), fetch-based API client.
- **KAN-26** home with category tiles, `/category/:id` product grid with stock badge, loading/empty/error states, responsive grid.
- **KAN-27** `/product/:id` with model, serial number, warranty, distributor, stock count, quantity selector; Add to cart is disabled (with tooltip) when stock is 0 and quantity is capped at stock.
- **KAN-29** guest cart in `localStorage` (Zustand `persist`), cart page with quantity +/- (capped at stock), remove, subtotal and navbar badge. Stock is re-checked when the cart page opens.

## Structure

```
src/
  components/   layout/, ui/ (shadcn-style primitives), shared pieces
  lib/          api client, catalog data access, helpers
  pages/        Home, Category, Product, Cart, NotFound
  store/        cart store
```
