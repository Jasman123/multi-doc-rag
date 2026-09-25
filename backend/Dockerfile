# Build context is the repo root (see railway.toml / `docker build -f backend/Dockerfile .`)
# so that both backend/ and frontend/ are available to COPY.

# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /install /usr/local
COPY backend/app/ ./backend/app/
COPY backend/alembic/ ./backend/alembic/
COPY backend/alembic.ini ./backend/alembic.ini
COPY frontend/ ./frontend/
COPY backend/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN mkdir -p ./backend/storage/chroma \
    && useradd -m -u 1000 appuser && chown -R appuser:appuser /app \
    && chmod +x /usr/local/bin/docker-entrypoint.sh
# Stays root here: mounted volumes (e.g. Railway's) land owned by root and
# shadow this chown, so the entrypoint re-chowns at boot before dropping to
# appuser — see docker-entrypoint.sh.
WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\", 8000)}/health')"
ENTRYPOINT ["docker-entrypoint.sh"]
# Railway injects PORT at runtime. Migrations run via railway.toml's
# deploy.preDeployCommand (once per deploy, also routed through the
# entrypoint above), not here, so scaling to multiple replicas can't race
# concurrent `alembic upgrade head` runs.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
