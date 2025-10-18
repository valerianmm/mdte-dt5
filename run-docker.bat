@echo off
setlocal enabledelayedexpansion

rem Change to script directory
cd /d "%~dp0"

rem Parse flags
set WITH_SIMULATOR=false
set ARGS=

:parse_args
if "%~1"=="" goto end_parse
if "%~1"=="-sim" (
    set WITH_SIMULATOR=true
    shift
) else (
    set ARGS=%ARGS% %1
    shift
)
goto parse_args
:end_parse

rem Compose files folder
set COMPOSE_DIR=./docker

rem Build the -f chain dynamically
set COMPOSE_FILES=
for %%f in (
    docker-compose.base.yml
    docker-compose.volumes.yml
    docker-compose.mqtt.yml
    docker-compose.spark.yml
) do (
    set COMPOSE_FILES=!COMPOSE_FILES! -f !COMPOSE_DIR!/%%f
)

rem Add simulator compose file if enabled
if "%WITH_SIMULATOR%"=="true" (
    set COMPOSE_FILES=!COMPOSE_FILES! -f !COMPOSE_DIR!/docker-compose.simulator.yml
)

rem Extract first argument
for /f "tokens=1*" %%a in ("%ARGS%") do (
    set COMMAND=%%a
    set REMAINING_ARGS=%%b
)

if "%COMMAND%"=="" goto up
if "%COMMAND%"=="up" goto up
if "%COMMAND%"=="down" goto down
if "%COMMAND%"=="restart" goto restart
if "%COMMAND%"=="pause" goto pause
if "%COMMAND%"=="unpause" goto unpause
if "%COMMAND%"=="ps" goto ps
if "%COMMAND%"=="build" goto build
if "%COMMAND%"=="logs" goto logs
goto unknown

:up
echo Starting stack...
if "%WITH_SIMULATOR%"=="true" (
    echo Running with simulator...
) else (
    echo Running without simulator...
)
docker compose %COMPOSE_FILES% up -d
goto :eof

:down
echo Stopping stack...
docker compose %COMPOSE_FILES% down
goto :eof

:restart
echo Restarting stack (fresh, volumes wiped^)...
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
echo Building services...
docker compose %COMPOSE_FILES% build %REMAINING_ARGS%
goto :eof

:logs
echo Showing logs...
docker compose %COMPOSE_FILES% logs %REMAINING_ARGS%
goto :eof

:unknown
echo [31m❌ Unknown command: %COMMAND%[0m
echo Usage: %~n0 [-sim] [up^|down^|restart^|pause^|unpause^|ps^|build^|logs]
echo   -sim: Run with the simulator service (default: off)
exit /b 1