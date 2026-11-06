# backend

Django + Django REST Framework API for Brewnook.

| Path | Purpose |
| --- | --- |
| `config/` | Django project package: URLs, WSGI/ASGI entry points, settings |
| `core/` | Cross-cutting endpoints such as the health check |
| `requirements.txt` | Pinned Python dependencies |
| `.env.example` | Template for `backend/.env` (local values only) |
| `pytest.ini` | pytest configuration (uses `config.settings.dev`) |

## Settings

`manage.py` defaults to `config.settings.dev`. WSGI/ASGI default to
`config.settings.prod`. Override with `DJANGO_SETTINGS_MODULE`.

| Variable | Used by | Description |
| --- | --- | --- |
| `SECRET_KEY` | all | Django secret key |
| `DATABASE_URL` | all | PostgreSQL connection URL |
| `CORS_ALLOWED_ORIGINS` | all | Comma-separated origins (dev defaults to the Vite server on port 5173) |
| `ALLOWED_HOSTS` | prod | Comma-separated host names (required) |

## Tests

```bash
pytest
```

## Health check

`GET /api/health` returns `{"status": "ok", "db": true}` when `SELECT 1`
succeeds against the database, and `"db": false` otherwise.
