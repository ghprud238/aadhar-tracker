# ==============================================================================
# Stage 1: Build virtual environment with uv
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy

# Install curl and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copy project specification files for dependency caching
COPY pyproject.toml uv.lock README.md ./

# Install production dependencies into standalone virtual environment
RUN uv sync --frozen --no-dev --no-install-project

# ==============================================================================
# Stage 2: Production Minimal Runtime
# ==============================================================================
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000 \
    WORKERS=2

# Install curl for container health probes
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create secure non-root service account
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/false -m appuser

# Copy virtualenv from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application packages and services
COPY pyproject.toml README.md alembic.ini ./
COPY packages/ ./packages/
COPY services/ ./services/
COPY apps/ ./apps/
COPY contracts/ ./contracts/
COPY docs/ ./docs/
COPY migrations/ ./migrations/
COPY docker-entrypoint.sh ./

# Adjust ownership to non-root appuser
RUN chmod +x /app/docker-entrypoint.sh && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Built-in container healthcheck compatible with Cloud Run, ECS, and Kubernetes
HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/livez || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
