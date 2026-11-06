# settings

Environment-split Django settings.

- `base.py`: shared settings; reads secrets and URLs from the environment.
- `dev.py`: local development (DEBUG on, Vite CORS origins, console email).
- `prod.py`: production (DEBUG off, `ALLOWED_HOSTS` from env, secure cookies, HSTS).
