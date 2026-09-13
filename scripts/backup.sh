#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/minedesso/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

echo "Starting backup at $TIMESTAMP..."

echo "Dumping PostgreSQL database..."
docker compose exec -T postgres pg_dumpall -U postgres > "$BACKUP_DIR/postgres_${TIMESTAMP}.sql"

echo "Backup complete."
ls -lh "$BACKUP_DIR"
