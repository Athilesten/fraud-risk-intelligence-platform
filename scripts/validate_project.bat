@echo off
setlocal
cd /d "%~dp0\.."

echo ============================================================
echo Fraud Risk Platform Validation
echo ============================================================

if not exist "venv\Scripts\python.exe" (
  echo ERROR: Python virtual environment not found.
  echo Fix:
  echo   py -3.11 -m venv venv
  echo   call venv\Scripts\activate.bat
  echo   pip install -r requirements-ci.txt
  echo   pip install -r streaming-requirements.txt
  exit /b 1
)

for /f "tokens=2" %%v in ('venv\Scripts\python.exe --version 2^>^&1') do set PY_VERSION=%%v
echo Python version: %PY_VERSION%
echo NOTE: Python 3.11 is recommended. Python 3.13 may fail for older ML wheels.

echo.
echo [1/5] Compiling backend and streaming files...
venv\Scripts\python.exe -m py_compile api\main.py || exit /b 1
venv\Scripts\python.exe -m py_compile src\db_logger.py || exit /b 1
venv\Scripts\python.exe -m py_compile src\big_data_views.py || exit /b 1
venv\Scripts\python.exe -m py_compile streaming\schema_validator.py || exit /b 1
venv\Scripts\python.exe -m py_compile streaming\kafka_producer.py || exit /b 1
venv\Scripts\python.exe -m py_compile streaming\kafka_scoring_consumer.py || exit /b 1
venv\Scripts\python.exe -m py_compile streaming\create_kafka_topics.py || exit /b 1
venv\Scripts\python.exe -m py_compile streaming\spark_streaming_delta_pipeline.py || exit /b 1
venv\Scripts\python.exe -m py_compile streaming\spark_scored_delta_pipeline.py || exit /b 1
venv\Scripts\python.exe -m py_compile streaming\read_delta_summary.py || exit /b 1

echo.
echo [2/5] Running tests...
venv\Scripts\python.exe -m pytest -q || exit /b 1

echo.
echo [3/5] Validating Docker Compose files...
docker compose -f docker-compose.app.yml config >nul || exit /b 1
docker compose -f docker-compose.streaming.yml config >nul || exit /b 1
echo Docker Compose config is valid.

echo.
echo [4/5] Installing frontend dependencies...
cd frontend
call npm.cmd install || exit /b 1

echo.
echo [5/5] Building frontend...
call npm.cmd run build || exit /b 1
cd ..

echo.
echo Validation complete: backend, tests, Docker config, and frontend build passed.
endlocal
