#!/usr/bin/env bash
set -euo pipefail
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.prod}"

python -m pip install -r requirements.txt
python manage.py collectstatic --noinput