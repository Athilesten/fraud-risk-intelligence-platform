@echo off
setlocal
cd /d "%~dp0\.."
set KAFKA_BOOTSTRAP_SERVERS=localhost:9092
set KAFKA_SCORED_TOPIC=transactions.scored
set DATA_LAKE_PATH=data/delta
set PYSPARK_PYTHON=%CD%\venv\Scripts\python.exe
set PYSPARK_DRIVER_PYTHON=%CD%\venv\Scripts\python.exe
.\venv\Scripts\python.exe streaming\spark_scored_delta_pipeline.py --once
endlocal
