@echo off
setlocal
cd /d "%~dp0\.."

if not exist "venv\Scripts\python.exe" (
  echo ERROR: venv\Scripts\python.exe not found.
  echo Create the environment with: py -3.11 -m venv venv
  exit /b 1
)

set KAFKA_BOOTSTRAP_SERVERS=localhost:9092
set KAFKA_RAW_TOPIC=transactions.raw
set KAFKA_SCORED_TOPIC=transactions.scored
set KAFKA_ERRORS_TOPIC=transactions.errors
set KAFKA_ERROR_TOPIC=transactions.errors

echo Creating Kafka topics on %KAFKA_BOOTSTRAP_SERVERS%...
venv\Scripts\python.exe streaming\create_kafka_topics.py
if errorlevel 1 (
  echo.
  echo ERROR: Kafka topics could not be created.
  echo Check:
  echo   docker compose -f docker-compose.streaming.yml ps
  echo   docker logs fraud_kafka --tail 80
  echo If Kafka just started, wait 60 seconds and run this script again.
  exit /b 1
)

echo Kafka topics are ready.
endlocal
