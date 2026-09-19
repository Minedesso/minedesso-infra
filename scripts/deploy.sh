#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

compose=(docker compose --env-file .env)
if [[ -f .minecraft-images.env ]]; then
  compose+=(--env-file .minecraft-images.env)
fi

echo "Pulling latest images..."
"${compose[@]}" pull

echo "Starting services..."
"${compose[@]}" up -d --wait --wait-timeout 300

echo "Deployment complete."
"${compose[@]}" ps
