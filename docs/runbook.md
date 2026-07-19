# Runbook

Use these commands from Windows Command Prompt.

Use Python 3.11 for the project virtual environment. Python 3.13 can fail when installing older ML wheels such as NumPy 1.x on Windows.

## 0. One-Time Local Setup

```cmd
cd D:\fraud-risk-intelligence-platform
py -3.11 -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements-ci.txt
pip install -r streaming-requirements.txt
cd frontend
npm install
npm run build
cd ..
```

## 1. Start App Stack

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\start_app_stack.bat
```

## 2. Start Kafka Stack

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\start_streaming_stack.bat
timeout /t 60
```

## 3. Create Kafka Topics

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\create_kafka_topics.bat
```

## 4. Optional: Generate Sample PaySim Data

Run this only if `data/raw/paysim.csv` is missing.

```cmd
cd D:\fraud-risk-intelligence-platform
.\venv\Scripts\python.exe scripts\generate_sample_paysim.py --rows 200
```

## 5. Optional: Run Alembic Migrations

The API still has safe startup table creation, but Alembic is the professional migration path.

```cmd
cd D:\fraud-risk-intelligence-platform
set DATABASE_URL=postgresql://fraud_user:fraud_password@localhost:5433/fraud_db
.\venv\Scripts\alembic.exe upgrade head
```

## 6. Run Kafka Demo

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\run_kafka_demo.bat
```

## 7. Optional: Run IEEE-CIS Producer

```cmd
cd D:\fraud-risk-intelligence-platform
.\venv\Scripts\python.exe streaming\kafka_producer.py --dataset ieee --max-records 20 --delay-seconds 0.2
```

## 8. Run Spark/Delta Demo

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\run_spark_delta_demo.bat
```

## 9. Optional: Run Raw Spark Pipeline Manually

For a bounded demo/validation run:

```cmd
cd D:\fraud-risk-intelligence-platform
.\venv\Scripts\python.exe streaming\spark_streaming_delta_pipeline.py --once
```

For continuous streaming mode, remove `--once`.

## 10. Optional: Run Scored Spark Pipeline Manually

For a bounded demo/validation run:

```cmd
cd D:\fraud-risk-intelligence-platform
.\venv\Scripts\python.exe streaming\spark_scored_delta_pipeline.py --once
```

For continuous streaming mode, remove `--once`.

## 11. Read Data Lake Summary

```cmd
cd D:\fraud-risk-intelligence-platform
.\venv\Scripts\python.exe streaming\read_delta_summary.py
```

## 12. Validate Project

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\validate_project.bat
```

## 13. Full Demo Shortcut

After dependencies are installed, this starts both stacks and runs Kafka plus Spark demos:

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\full_demo.bat
```

## 14. Open URLs

- React product UI: http://localhost:3001
- FastAPI docs: http://localhost:8000/docs
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Kafka UI: http://localhost:8080
- Streamlit internal dashboard: http://localhost:8501

## 15. Stop Services

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\stop_all.bat
```
