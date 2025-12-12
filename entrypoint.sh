#!/usr/bin/env bash
set -e

# run alembic migrations
if [ -n "${DATABASE_URL-}" ]; then
  alembic upgrade head || true
fi

# start app
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

