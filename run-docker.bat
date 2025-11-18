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
    set COMPOSE_PROFILES=simulator
    shift
) else (
    set ARGS=%ARGS% %1
    shift
)
goto parse_args
:end_parse

rem Single compose file
set COMPOSE_FILE=docker/docker-compose.base.yml

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
docker compose -f %COMPOSE_FILE% up -d
goto :eof

:down
echo Stopping stack...
docker compose -f %COMPOSE_FILE% down
goto :eof

:restart
echo Restarting stack (fresh, volumes wiped^)...
docker compose -f %COMPOSE_FILE% down -v
docker compose -f %COMPOSE_FILE% up -d
goto :eof

:pause
echo Pausing all containers...
docker compose -f %COMPOSE_FILE% pause
goto :eof

:unpause
echo Unpausing all containers...
docker compose -f %COMPOSE_FILE% unpause
goto :eof

:ps
docker compose -f %COMPOSE_FILE% ps
goto :eof

:build
echo Building services...
docker compose -f %COMPOSE_FILE% build %REMAINING_ARGS%
goto :eof

:logs
echo Showing logs...
docker compose -f %COMPOSE_FILE% logs %REMAINING_ARGS%
goto :eof

:unknown
echo [31m❌ Unknown command: %COMMAND%[0m
echo Usage: %~n0 [-sim] [up^|down^|restart^|pause^|unpause^|ps^|build^|logs]
echo   -sim: Run with the simulator service (default: off)
exit /b 1