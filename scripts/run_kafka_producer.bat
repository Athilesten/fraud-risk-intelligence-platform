@echo off
cd /d "%~dp0\.."
set KAFKA_BOOTSTRAP_SERVERS=localhost:9092
set KAFKA_RAW_TOPIC=transactions.raw
.\venv\Scripts\python.exe streaming\kafka_producer.py --dataset paysim --max-records 20 --delay-seconds 0.2
