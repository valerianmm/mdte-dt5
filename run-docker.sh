#!/usr/bin/env bash
set -e

# Move into script directory (so it works regardless of where you run it)
cd "$(dirname "$0")"

# Compose files folder
COMPOSE_DIR="./docker"

# Build the -f chain dynamically
COMPOSE_FILES=""
for f in \
  docker-compose.base.yml \
  docker-compose.volumes.yml \
  mqtt/docker-compose.mqtt.yml \
  # airflow/docker-compose.airflow.yml
do
  COMPOSE_FILES="$COMPOSE_FILES -f $COMPOSE_DIR/$f"
done

# Default command is "up -d"
CMD="up -d"

# Allow passing extra args (e.g., ./run.sh down)
if [ $# -gt 0 ]; then
  CMD="$*"
fi

echo "Running: docker compose $COMPOSE_FILES $CMD"
docker compose $COMPOSE_FILES $CMD
