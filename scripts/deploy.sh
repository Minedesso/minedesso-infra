#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Pulling latest images..."
docker compose pull

echo "Starting services..."
docker compose up -d

echo "Deployment complete."
docker compose ps
