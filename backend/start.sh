#!/usr/bin/env bash
set -euo pipefail
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.prod}"

python manage.py migrate --noinput

exec daphne \
  -b 0.0.0.0 \
  -p "${PORT:-8000}" \
  config.asgi:application