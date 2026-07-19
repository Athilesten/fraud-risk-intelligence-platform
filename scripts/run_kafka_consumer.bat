@echo off
cd /d "%~dp0\.."
set KAFKA_BOOTSTRAP_SERVERS=localhost:9092
set KAFKA_RAW_TOPIC=transactions.raw
set KAFKA_SCORED_TOPIC=transactions.scored
set KAFKA_ERRORS_TOPIC=transactions.errors
set FRAUD_API_URL=http://127.0.0.1:8000/predict
set FRAUD_API_KEY=dev_fraud_api_key_123
set MAX_API_RETRIES=3
.\venv\Scripts\python.exe streaming\kafka_scoring_consumer.py --max-records 20
