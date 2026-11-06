# accounts

Custom user model and account-related code.

- `models.py`: `User` (email login, `full_name` as the only name field,
  `tax_id`, `home_address`, `role`).
- `managers.py`: `UserManager` with email-based `create_user` / `create_superuser`.

Roles (`User.Role`): `customer` (default), `sales_manager`,
`product_manager`, `support_agent`.
