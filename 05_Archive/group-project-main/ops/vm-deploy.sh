#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${APP_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
IMAGE_NAME="${IMAGE_NAME:-group-project-vm}"
CONTAINER_NAME="${CONTAINER_NAME:-group-project-vm}"
HOST_PORT="${HOST_PORT:-8080}"
CONTAINER_PORT="${CONTAINER_PORT:-8080}"

cd "${APP_DIR}"
APP_REVISION="$(git rev-parse --short HEAD 2>/dev/null || echo dev)"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed on this VM." >&2
  exit 1
fi

if [ ! -f ".env" ]; then
  echo "Missing ${APP_DIR}/.env. Create it from .env.example before deploying." >&2
  exit 1
fi

docker build --build-arg "APP_REVISION=${APP_REVISION}" -t "${IMAGE_NAME}:latest" .
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker run -d \
  --restart unless-stopped \
  --name "${CONTAINER_NAME}" \
  --env-file "${APP_DIR}/.env" \
  -p "${HOST_PORT}:${CONTAINER_PORT}" \
  "${IMAGE_NAME}:latest"

docker image prune -f >/dev/null 2>&1 || true
docker ps --filter "name=${CONTAINER_NAME}"
docker exec "${CONTAINER_NAME}" sh -lc 'printf "Container app revision: %s\n" "${APP_REVISION:-unknown}"; head -1 /app/frontend/sw.js'
