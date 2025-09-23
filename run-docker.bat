@echo off
setlocal enabledelayedexpansion

rem Change to script directory
cd /d "%~dp0"

rem Compose files folder
set COMPOSE_DIR=.\docker

rem Build the -f chain dynamically
set COMPOSE_FILES=
for %%f in (
    docker-compose.base.yml
    docker-compose.volumes.yml
    docker-compose.mqtt.yml
    docker-compose.spark.yml
    docker-compose.simulator.yml
) do (
    set "COMPOSE_FILES=!COMPOSE_FILES! -f %COMPOSE_DIR%\%%f"
)

rem Default command is "up" if none provided
if "%1"=="" goto :up
goto :%1

:up
echo Starting stack...
docker compose %COMPOSE_FILES% up -d
goto :eof

:down
echo Stopping stack...
docker compose %COMPOSE_FILES% down
goto :eof

:restart
echo Restarting stack (fresh, volumes wiped)...
docker compose %COMPOSE_FILES% down -v
docker compose %COMPOSE_FILES% up -d
goto :eof

:pause
echo Pausing all containers...
docker compose %COMPOSE_FILES% pause
goto :eof

:unpause
echo Unpausing all containers...
docker compose %COMPOSE_FILES% unpause
goto :eof

:ps
docker compose %COMPOSE_FILES% ps
goto :eof

:build
shift
echo Building services...
docker compose %COMPOSE_FILES% build %*
goto :eof

:logs
shift
echo Showing logs...
docker compose %COMPOSE_FILES% logs %*
goto :eof

rem If no valid command is provided
echo ❌ Unknown command: %1
echo Usage: %0 [up^|down^|restart^|pause^|unpause^|ps^|build^|logs]
echo Simulator service is included by default.
exit /b 1