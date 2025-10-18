#!/usr/bin/env bash
set -e

# Move into script directory (so it works regardless of where you run it)
cd "$(dirname "$0")"

# Parse flags
WITH_SIMULATOR=false
ARGS=()
for arg in "$@"; do
  case $arg in
    -sim)
      WITH_SIMULATOR=true
      shift
      ;;
    *)
      ARGS+=("$arg")
      ;;
  esac
done

# Compose files folder
COMPOSE_DIR="./docker"

# Build the -f chain dynamically
COMPOSE_FILES=""
for f in \
  docker-compose.base.yml \
  docker-compose.volumes.yml \
  docker-compose.mqtt.yml \
  docker-compose.spark.yml
do
  COMPOSE_FILES="$COMPOSE_FILES -f $COMPOSE_DIR/$f"
done

# Add simulator compose file if enabled
if [ "$WITH_SIMULATOR" = true ]; then
  COMPOSE_FILES="$COMPOSE_FILES -f $COMPOSE_DIR/docker-compose.simulator.yml"
fi

# Helper: run docker compose with all files
dc() {
  docker compose $COMPOSE_FILES "$@"
}

# Commands
case "${ARGS[0]:-}" in
  ""|up)
    echo "Starting stack..."
    if [ "$WITH_SIMULATOR" = true ]; then
      echo "Running with simulator..."
    else
      echo "Running without simulator..."
    fi
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
    dc build "${ARGS[@]:1}"
    ;;
  logs)
    shift
    echo "Showing logs..."
    dc logs "${ARGS[@]:1}"
    ;;
  *)
    echo "❌ Unknown command: ${ARGS[0]}"
    echo "Usage: $0 [-sim] [up|down|restart|pause|unpause|ps|build|logs]"
    echo "  -sim: Run with the simulator service (default: off)"
    exit 1
    ;;
esac
