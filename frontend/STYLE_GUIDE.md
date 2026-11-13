# Brewnook style guide (KAN-30)

Short reference for building Brewnook pages so they look and behave the same.
To see everything live, run `npm run dev` and open **http://localhost:5173/styleguide** (development only).

Tokens live in `src/styles/theme.css`. Shared components live in `src/components/common/`.

## Colors

Coffee-inspired palette. Always use the Tailwind token classes (`bg-primary`, `text-muted-foreground`, ...),
never raw hex values in components, so a palette change only touches `theme.css`.

| Token | Hex | Use for |
| --- | --- | --- |
| `background` | `#faf6f1` | Page background (cream) |
| `foreground` | `#2b1d14` | Main text (espresso) |
| `card` | `#ffffff` | Cards, panels, dialogs, toasts |
| `primary` | `#4a2c1a` | Main buttons, prices, active links (dark roast) |
| `secondary` | `#efe5d8` | Secondary buttons, image placeholders (latte) |
| `muted` / `muted-foreground` | `#f1e9df` / `#6f5c4e` | Subtle backgrounds / secondary text |
| `accent` | `#c8843c` | Fills and icons only: cart badge, focus ring, logo (caramel) |
| `accent-strong` | `#9a5b1f` | Caramel **text** (category labels, small highlights) |
| `success` | `#276b43` | In stock, completed, delivered |
| `warning` | `#92400e` | Low stock, pending, attention needed |
| `destructive` | `#b3261e` | Out of stock, errors, delete actions |
| `border` / `input` | `#e4d6c5` / `#d9c8b3` | Borders / form field borders |

Rules:

- **Status colors** go on a 10% tint of themselves: `text-success bg-success/10 border-success/30`.
- **Don't use `accent` for text** on light backgrounds; it fails contrast. Use `accent-strong`.
- All text/background pairs above pass WCAG AA (4.5:1), which KAN-69's Lighthouse accessibility target (≥ 90) needs.
  If you change a color, re-check its contrast.

## Typography

One sans-serif family (`font-sans`). Use the named text styles instead of choosing sizes per page:

| Class | Size | Use for |
| --- | --- | --- |
| `type-display` | 30 → 36 px, bold | Hero headline on the home page only |
| `type-title` | 24 px, bold | Page `<h1>` (category name, "Your cart", "Search") |
| `type-heading` | 20 px, semibold | Section `<h2>` |
| `type-body` | 16 px, relaxed | Paragraphs, product descriptions |
| `type-caption` | 14 px, muted | Hints, helper text, metadata |

Keep heading levels in order (one `<h1>` per page, then `<h2>`, ...); screen readers and Lighthouse check this.

## Components

Import from `@/components/common/...`.

| Component | Use | Example |
| --- | --- | --- |
| `ProductCard` | Product tile in any grid; whole card links to the product | `<ProductCard product={p} />` |
| `ProductGrid` | Responsive grid of ProductCards (1 → 2 → 3 → 4 columns) | `<ProductGrid products={list} />` |
| `PriceTag` | Any price shown to customers, in TRY. Pass `originalPrice` for discounts | `<PriceTag price={472} originalPrice={590} size="lg" />` |
| `StockBadge` | Stock level. `0` → "Out of stock", `1–5` → "Only N left", more → "In stock: N" | `<StockBadge stock={p.stock} />` |
| `EmptyState` | Empty lists: no results, empty cart, no orders | `<EmptyState title="Your cart is empty" action={<Button>Shop</Button>} />` |
| `ProductGridSkeleton`, `ProductCardSkeleton` | Loading placeholders with the same layout as the real content | `{loading && <ProductGridSkeleton />}` |
| `toast` + `Toaster` | Short confirmations and errors after an action | `toast.success('Added to cart')` |

### Manager area (`/manage`)

| Component | Use |
| --- | --- |
| `DataTable` (`@/components/manage/DataTable`) | Every list in the manager area. Give columns a `sortValue` to make them sortable; rows are paged (`pageSize`, default 10). Pass `loading` and `empty`. |
| `ConfirmDialog` (`@/components/common/ConfirmDialog`) | Before deleting or any action that can't be undone. If `onConfirm` returns a promise, the button shows "Working…" and the dialog closes only when it succeeds. |

New manager sections are added in one place, `src/lib/manage-nav.ts` (path, label, icon, which roles see it), and get
their page in `MANAGE_PAGES` in `App.tsx`. The sidebar, overview cards and role checks follow automatically.

Base building blocks (buttons, badges, cards, alerts, tooltips) are shadcn/ui components in `src/components/ui/`.
Use `Button` variants rather than styling buttons by hand: `default` for the main action, `outline`/`secondary`
for secondary actions, `destructive` for delete, `ghost` for icon-only buttons.

### Toasts

```ts
import { toast } from '@/lib/toast'

toast.success('Added to cart')          // green check, 4 s
toast.error('Could not reach the server.') // red, 7 s, announced immediately by screen readers
toast('Signed out')                     // neutral, 4 s
```

`<Toaster />` is already mounted in `Layout`; don't add another. Use toasts for feedback on an action the user just
took. For errors that block the page (a list failed to load), use `ErrorState` in the page instead.

## Page patterns

Every page that loads data handles all four states, in this order:

1. **Loading** → skeleton (`ProductGridSkeleton`, or `Skeleton` blocks shaped like the content)
2. **Error** → `<ErrorState message="..." onRetry={reload} />`
3. **Empty** → `<EmptyState ... />`
4. **Data** → the content

Spacing: pages use `space-y-6` between blocks, grids use `gap-4`, cards use `p-4`. Corners come from `--radius`
(`rounded-lg`, `rounded-xl`), so don't hard-code pixel radii.
