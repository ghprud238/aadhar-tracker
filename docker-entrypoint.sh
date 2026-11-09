#!/bin/sh
set -e

# Run database schema migrations if requested or on initial startup
if [ "$RUN_MIGRATIONS" = "true" ] || [ "$RUN_MIGRATIONS" = "1" ]; then
    echo "[*] Running database migrations (alembic upgrade head)..."
    python -m alembic upgrade head || echo "[!] Warning: Migration step failed or skipped."
fi

# If a specific command was passed to docker run, execute that instead
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

# Default: Launch production FastAPI server with dynamic PORT and WORKERS
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-2}"

echo "[*] Starting Suraksha Platform API on port $PORT with $WORKERS worker(s)..."
exec python -m uvicorn services.api.main:app --host 0.0.0.0 --port "$PORT" --workers "$WORKERS"
