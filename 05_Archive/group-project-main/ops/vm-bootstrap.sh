#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${1:-}"
APP_DIR="${APP_DIR:-/opt/group-project}"

if [ -z "${REPO_URL}" ]; then
  echo "Usage: ./ops/vm-bootstrap.sh <github-repo-url>" >&2
  echo "Example: ./ops/vm-bootstrap.sh https://github.com/OWNER/REPO.git" >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y git docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker "${USER}" || true

sudo mkdir -p "$(dirname "${APP_DIR}")"
sudo chown -R "${USER}:${USER}" "$(dirname "${APP_DIR}")"

if [ ! -d "${APP_DIR}/.git" ]; then
  git clone "${REPO_URL}" "${APP_DIR}"
else
  git -C "${APP_DIR}" fetch origin
  git -C "${APP_DIR}" reset --hard origin/main
fi

cd "${APP_DIR}"
chmod +x ops/vm-deploy.sh ops/vm-cron-sync-new.sh

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created ${APP_DIR}/.env. Fill it with production values, then run: ./ops/vm-deploy.sh"
else
  ./ops/vm-deploy.sh
fi
