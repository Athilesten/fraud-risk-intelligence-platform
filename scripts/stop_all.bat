@echo off
setlocal
cd /d "%~dp0\.."

echo Stopping app stack...
docker compose -f docker-compose.app.yml down

echo.
echo Stopping streaming stack...
docker compose -f docker-compose.streaming.yml down

echo.
echo All local fraud platform containers have been stopped.
endlocal
