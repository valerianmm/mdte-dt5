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
  docker-compose.mqtt.yml \
  docker-compose.spark.yml \
  docker-compose.simulator.yml

do
  COMPOSE_FILES="$COMPOSE_FILES -f $COMPOSE_DIR/$f"
done

# Helper: run docker compose with all files
dc() {
  docker compose $COMPOSE_FILES "$@"
}

# Commands
case "${1:-}" in
  ""|up)
    echo "Starting stack..."
    dc up -d
    ;;
  down)
    echo "Stopping stack..."
    dc down
    ;;
  restart)
    echo "Restarting stack (fresh, volumes wiped)..."
    dc down -v
    dc up -d
    ;;
  pause)
    echo "Pausing all containers..."
    dc pause
    ;;
  unpause)
    echo "Unpausing all containers..."
    dc unpause
    ;;
  ps)
    dc ps
    ;;
  build)
    shift
    echo "Building services..."
    dc build "$@"
    ;;
  logs)
    shift
    echo "Showing logs..."
    dc logs "$@"
    ;;
  *)
    echo "❌ Unknown command: $1"
    echo "Usage: $0 [up|down|restart|pause|unpause|ps|build|logs]"
    exit 1
    ;;
esac
