# Role matrix

API access by role. Roles are defined in `backend/accounts/models.py`
(`User.Role`); permission classes live in `backend/accounts/permissions.py`.

## Rules

- **Deny by default.** `DEFAULT_PERMISSION_CLASSES` is `IsAuthenticated`.
  Every public endpoint must declare `AllowAny` explicitly.
- **Role checks are exact.** `IsCustomer`, `IsSalesManager`,
  `IsProductManager` and `IsSupportAgent` allow only active users whose
  `role` matches. Superusers get no implicit bypass.
- **Shared endpoints** combine classes: `[IsSalesManager | IsProductManager]`.
- Unauthenticated requests receive `401`; authenticated users without the
  required role receive `403`.

## Endpoints

Legend: ✅ allowed · ❌ denied (403) · 🌐 public (no login needed)

| Endpoint | Anonymous | Customer | Sales manager | Product manager | Support agent | Permission |
| --- | :---: | :---: | :---: | :---: | :---: | --- |
| `GET /api/health` | 🌐 | 🌐 | 🌐 | 🌐 | 🌐 | `AllowAny` |
| `GET /api/products/`, `/api/products/{id}/` | 🌐 | 🌐 | 🌐 | 🌐 | 🌐 | `AllowAny` |
| `GET /api/categories/` | 🌐 | 🌐 | 🌐 | 🌐 | 🌐 | `AllowAny` |
| `POST /api/auth/register`, `login`, `refresh`, `logout` | 🌐 | 🌐 | 🌐 | 🌐 | 🌐 | `AllowAny` |
| `GET /api/auth/me` | ❌ 401 | ✅ | ✅ | ✅ | ✅ | `IsAuthenticated` |
| `POST /api/payments/mock` (KAN-42) | ❌ 401 | ✅ | ❌ | ❌ | ❌ | `IsCustomer` |
| `GET /api/deliveries` (KAN-45) | ❌ 401 | ❌ | ❌ | ✅ | ❌ | `IsProductManager` |
| `PATCH /api/deliveries/{id}/complete` (KAN-45) | ❌ 401 | ❌ | ❌ | ✅ | ❌ | `IsProductManager` |
| `PATCH /api/orders/{id}/status` (KAN-45) | ❌ 401 | ❌ | ❌ | ✅ | ❌ | `IsProductManager` |

Rows marked with a ticket key are added by that ticket's PR.

## Planned (not implemented yet)

Responsibilities from the project README, to be mapped to endpoints when
they are built:

| Role | Responsibilities |
| --- | --- |
| Customer | Cart, checkout, profile, reviews, wishlist, order tracking |
| Product manager | Products and categories, inventory, comment moderation, deliveries |
| Sales manager | Prices and discounts, invoices, revenue and profit/loss reports, return approval |
| Support agent | Live support conversations and customer context |

## Tests

`backend/accounts/test_permissions.py` checks every role against every
role's sample endpoint (own role → 200, other roles → 403, anonymous → 401).
`backend/accounts/test_public_endpoints.py` checks that public endpoints
stay reachable without login.
