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

java -version >nul 2>nul
if errorlevel 1 (
  echo ERROR: Java is required for Spark.
  echo Install JDK 17, reopen CMD, and confirm with: java -version
  exit /b 1
)

set KAFKA_BOOTSTRAP_SERVERS=localhost:9092
set KAFKA_RAW_TOPIC=transactions.raw
set KAFKA_SCORED_TOPIC=transactions.scored
set DATA_LAKE_PATH=data/delta
set PYSPARK_PYTHON=%CD%\venv\Scripts\python.exe
set PYSPARK_DRIVER_PYTHON=%CD%\venv\Scripts\python.exe

echo Running Spark raw Bronze/Silver/Gold pipeline once...
venv\Scripts\python.exe streaming\spark_streaming_delta_pipeline.py --once || exit /b 1

echo.
echo Running Spark scored decision pipeline once...
venv\Scripts\python.exe streaming\spark_scored_delta_pipeline.py --once || exit /b 1

echo.
echo Reading Delta summary...
venv\Scripts\python.exe streaming\read_delta_summary.py || exit /b 1

echo.
echo Spark/Delta demo completed.
endlocal
