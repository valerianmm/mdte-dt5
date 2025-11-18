#!/usr/bin/env bash
set -e

# Move into script directory
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

# Set simulator profile if enabled
if [ "$WITH_SIMULATOR" = true ]; then
  export COMPOSE_PROFILES=simulator
fi

# Compose file
COMPOSE_FILE="docker/docker-compose.base.yml"

# Helper: run docker compose
dc() {
  docker compose -f $COMPOSE_FILE "$@"
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
