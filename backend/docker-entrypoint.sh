#!/bin/sh
set -e

# Persistent volumes (Railway, Docker, ...) are mounted owned by root, which
# shadows the image's chown and leaves appuser unable to write into them.
# Fix ownership once at boot, as root, then drop to appuser for the real
# command (uvicorn, or `alembic upgrade head` as Railway's pre-deploy step).
mkdir -p /app/backend/storage/chroma
chown -R appuser:appuser /app/backend/storage

exec runuser -u appuser -- "$@"
