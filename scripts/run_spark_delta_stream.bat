@echo off
setlocal
cd /d "%~dp0\.."
set KAFKA_BOOTSTRAP_SERVERS=localhost:9092
set KAFKA_RAW_TOPIC=transactions.raw
set DATA_LAKE_PATH=data/delta
set PYSPARK_PYTHON=%CD%\venv\Scripts\python.exe
set PYSPARK_DRIVER_PYTHON=%CD%\venv\Scripts\python.exe
.\venv\Scripts\python.exe streaming\spark_streaming_delta_pipeline.py --once
endlocal
