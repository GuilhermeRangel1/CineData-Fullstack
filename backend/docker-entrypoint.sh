#!/bin/sh
set -eu

alembic upgrade head
python -m app.db.seed --database-url "${DATABASE_URL}"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
