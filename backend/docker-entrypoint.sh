#!/bin/sh
set -eu

alembic upgrade head
python -m app.db.seed --database-url "${DATABASE_URL}"

if [ -n "${INITIAL_ADMIN_EMAIL:-}" ] || [ -n "${INITIAL_ADMIN_NAME:-}" ] || [ -n "${INITIAL_ADMIN_PASSWORD:-}" ]; then
  python -m app.users.bootstrap_admin
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
