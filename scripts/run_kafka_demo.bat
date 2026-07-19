@echo off
setlocal
cd /d "%~dp0\.."

if not exist "venv\Scripts\python.exe" (
  echo ERROR: venv\Scripts\python.exe not found.
  echo Fix:
  echo   py -3.11 -m venv venv
  echo   call venv\Scripts\activate.bat
  exit /b 1
)

echo Checking FastAPI health...
curl -fsS http://127.0.0.1:8000/health >nul
if errorlevel 1 (
  echo ERROR: FastAPI is not reachable at http://127.0.0.1:8000.
  echo Start it first: scripts\start_app_stack.bat
  exit /b 1
)

echo Creating Kafka topics...
call scripts\create_kafka_topics.bat || exit /b 1

if not exist "data\raw\paysim.csv" (
  echo PaySim sample data is missing. Generating a small local sample...
  venv\Scripts\python.exe scripts\generate_sample_paysim.py || exit /b 1
)

echo Publishing 20 PaySim transactions to Kafka...
venv\Scripts\python.exe streaming\kafka_producer.py --dataset paysim --max-records 20 --delay-seconds 0.2 || exit /b 1

echo Scoring 20 Kafka transactions through FastAPI...
set FRAUD_API_KEY=dev_fraud_api_key_123
set API_BASE_URL=http://127.0.0.1:8000
set FRAUD_API_URL=http://127.0.0.1:8000/predict
venv\Scripts\python.exe streaming\kafka_scoring_consumer.py --max-records 20 || exit /b 1

echo.
echo Kafka fraud streaming demo completed.
echo Check React: http://localhost:3001
echo Check Kafka UI: http://localhost:8080
endlocal
