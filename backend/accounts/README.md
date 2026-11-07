# accounts

Custom user model and account-related code.

- `models.py`: `User` (email login, `full_name` as the only name field,
  `tax_id`, `home_address`, `role`).
- `managers.py`: `UserManager` with email-based `create_user` / `create_superuser`.
- `serializers.py`, `views.py`, `urls.py`: auth API under `/api/auth/`.
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

Access tokens live 15 minutes, refresh tokens 7 days (`SIMPLE_JWT` in
`config/settings/base.py`). The refresh cookie is scoped to `/api/auth/`.
The frontend must send requests with credentials (`credentials: "include"`)
for the cookie to be stored and sent.
