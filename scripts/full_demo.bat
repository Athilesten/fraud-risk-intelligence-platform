@echo off
setlocal
cd /d "%~dp0\.."

echo ============================================================
echo Real-Time Fraud Risk Intelligence Platform - Full Demo
echo ============================================================

if not exist "venv\Scripts\python.exe" (
  echo ERROR: Python venv not found.
  echo Run:
  echo   py -3.11 -m venv venv
  echo   call venv\Scripts\activate.bat
  echo   pip install -r requirements-ci.txt
  echo   pip install -r streaming-requirements.txt
  exit /b 1
)

if not exist ".env" (
  echo .env not found. Creating it from .env.example...
  copy .env.example .env >nul || exit /b 1
)

if not exist "frontend\.env" (
  echo frontend\.env not found. Creating it from frontend\.env.example...
  copy frontend\.env.example frontend\.env >nul || exit /b 1
)

echo.
echo [1/6] Starting application stack...
call scripts\start_app_stack.bat || exit /b 1
echo Waiting for FastAPI...
timeout /t 30

echo.
echo [2/6] Checking FastAPI health...
curl -fsS http://127.0.0.1:8000/health || exit /b 1

echo.
echo [3/6] Starting Kafka stack...
call scripts\start_streaming_stack.bat || exit /b 1
echo Waiting for Kafka broker readiness...
timeout /t 60

echo.
echo [4/6] Running Kafka fraud scoring demo...
call scripts\run_kafka_demo.bat || exit /b 1

echo.
echo [5/6] Running Spark/Delta lakehouse demo...
call scripts\run_spark_delta_demo.bat || exit /b 1

echo.
echo [6/6] Final URLs
echo React product UI:   http://localhost:3001
echo FastAPI docs:       http://localhost:8000/docs
echo Streamlit internal: http://localhost:8501
echo Prometheus:         http://localhost:9090
echo Grafana:            http://localhost:3000
echo Kafka UI:           http://localhost:8080
echo.
echo Full demo completed successfully.
endlocal
