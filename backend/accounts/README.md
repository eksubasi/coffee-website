# accounts

Custom user model and account-related code.

- `models.py`: `User` (email login, `full_name` as the only name field,
  `tax_id`, `home_address`, `role`).
- `managers.py`: `UserManager` with email-based `create_user` / `create_superuser`.
- `serializers.py`, `views.py`, `urls.py`: auth API under `/api/auth/`.
- `throttling.py`: rate limits for login (per IP and per email) and register (per IP).
- `permissions.py`: `IsCustomer`, `IsSalesManager`, `IsProductManager`,
  `IsSupportAgent` (see `docs/role-matrix.md`).
- `management/commands/seed_users.py`: demo users, one per role.

Roles (`User.Role`): `customer` (default), `sales_manager`,
`product_manager`, `support_agent`.

## Auth API (`/api/auth/`)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `register` | none | Create a customer account (`email`, `password`, optional `full_name`, `tax_id`, `home_address`). Role is always `customer`. |
| POST | `login` | none | Returns `{"access", "user"}`; sets the refresh token as an httpOnly cookie. |
| POST | `refresh` | refresh cookie | Returns a new `access`; rotates the cookie and blacklists the old refresh token. |
| POST | `logout` | refresh cookie (optional) | Blacklists the refresh token and clears the cookie. |
| GET | `me` | `Authorization: Bearer <access>` | Current user. |
| POST | `password-reset` | none | `{"email"}`. Always `202` with the same message; if an active account exists, a reset link is emailed. |
| POST | `password-reset/confirm` | none | `{"uid", "token", "new_password"}`. `200` on success; `400` with `detail` for an invalid/expired/used link, or with `new_password` errors from the Django password validators. |

Access tokens live 15 minutes, refresh tokens 7 days (`SIMPLE_JWT` in
`config/settings/base.py`). The refresh cookie is scoped to `/api/auth/`.
The frontend must send requests with credentials (`credentials: "include"`)
for the cookie to be stored and sent.

### Rate limits

| Endpoint | Limit | Key |
| --- | --- | --- |
| `login` | 5/min | client IP |
| `login` | 5/min | email (case-insensitive) |
| `register` | 3/min | client IP |

Every attempt counts, successful or not. Over the limit the API returns
`429` with a `Retry-After` header (seconds). Rates are in
`REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`; counters live in the Django
cache. The client IP is `REMOTE_ADDR` unless `DRF_NUM_PROXIES` is set.

### Account enumeration

Responses never reveal whether an email is registered:

- Login: one message for unknown email, wrong password and inactive account.
- Register: a taken email returns `400 {"detail": "..."}` with a generic
  message, checked only after all field validation passes.
- Password reset: always `202` with the same body.

### Password reset

Tokens come from Django's `default_token_generator`; the link carries
`uid` (base64 user id) and `token`. A token stops working after
`PASSWORD_RESET_TIMEOUT` (1 hour), once the password changes (single use),
or once the user logs in again (it hashes `last_login`). A successful reset
blacklists all of the user's refresh tokens. In development the email is
printed to the backend console.
