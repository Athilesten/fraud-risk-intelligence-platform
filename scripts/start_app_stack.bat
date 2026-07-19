@echo off
setlocal
cd /d "%~dp0\.."

echo Starting Fraud Risk app stack...
docker info >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker Desktop is not running or Docker is unavailable.
  echo Start Docker Desktop, wait until it is ready, then run this script again.
  exit /b 1
)

if not exist ".env" (
  echo .env not found. Creating it from .env.example...
  copy .env.example .env >nul || exit /b 1
)

docker compose -f docker-compose.app.yml up -d || exit /b 1
docker compose -f docker-compose.app.yml ps

echo.
echo App stack requested. Wait 20-30 seconds, then check:
echo   curl http://localhost:8000/health
echo   http://localhost:3001
endlocal
