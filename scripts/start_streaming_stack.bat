@echo off
setlocal
cd /d "%~dp0\.."

echo Starting Kafka streaming stack...
docker info >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker Desktop is not running or Docker is unavailable.
  echo Start Docker Desktop, wait until it is ready, then run this script again.
  exit /b 1
)

docker compose -f docker-compose.streaming.yml up -d || exit /b 1
docker compose -f docker-compose.streaming.yml ps

echo.
echo Kafka usually needs 45-60 seconds before clients can connect.
echo Next:
echo   timeout /t 60
echo   scripts\create_kafka_topics.bat
endlocal
