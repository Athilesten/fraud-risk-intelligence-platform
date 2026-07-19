# Load Testing

This folder contains a Locust workload for the local FastAPI fraud scoring service.

## Install

```cmd
cd D:\fraud-risk-intelligence-platform
call venv\Scripts\activate.bat
pip install locust
```

## Interactive Run

```cmd
locust -f load_tests\locustfile.py --host=http://localhost:8000
```

Open:

```text
http://localhost:8089
```

## Headless Run

```cmd
locust -f load_tests\locustfile.py --host=http://localhost:8000 --users 20 --spawn-rate 5 --run-time 2m --headless
```

## What It Tests

- `GET /health`
- `POST /predict`
- `POST /predict_batch`
- `GET /prediction_logs`
- `GET /monitoring/metrics`

Run this only after the app stack is healthy.
