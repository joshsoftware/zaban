#!/usr/bin/env bash
# Run docker compose; automatically use GPU override when NVIDIA container runtime is available.
# Usage: ./compose.sh up -d   (same as docker compose up -d, but GPU-enabled on supported hosts)

set -e

COMPOSE_CMD="${COMPOSE_CMD:-docker compose}"
if ! $COMPOSE_CMD version &>/dev/null; then
  COMPOSE_CMD="docker-compose"
fi

COMPOSE_FILES="-f docker-compose.yml"
if docker info 2>/dev/null | grep -qi nvidia; then
  COMPOSE_FILES="-f docker-compose.yml -f docker-compose.gpu.yml"
  echo "NVIDIA runtime detected — using GPU override."
fi

exec $COMPOSE_CMD $COMPOSE_FILES "$@"
