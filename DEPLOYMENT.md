# Deployment Checklist

## Local Production-Style Stack

1. Copy `.env.example` to `.env`.
2. Set strong secrets.
3. Confirm model artifacts exist in `models/`.
4. Start the application stack:

```bash
docker compose -f docker-compose.app.yml up --build
```

5. Open:

- FastAPI docs: `http://localhost:8000/docs`
- Streamlit dashboard: `http://localhost:8501`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## Required Environment Variables

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `DATABASE_URL`
- `FRAUD_API_KEY`
- `FRAUD_CORS_ORIGINS`
- `API_BASE_URL`
- `GRAFANA_ADMIN_USER`
- `GRAFANA_ADMIN_PASSWORD`

## Pre-Deployment Checks

- tests pass with `python -m pytest`
- dependencies are pinned
- `.env` is not committed
- `node_modules/` is not committed
- model metadata and retraining report are current
- threshold policy is documented
- rollback model artifact is available
- dashboard access is restricted

## Operational Monitoring

Prometheus metrics are exposed at `/metrics`.

Track:

- request count
- error rate
- latency
- prediction count by risk level
- final decision distribution
- fraud probability distribution

## Model Operations

The Airflow DAG retrains weekly. Before promoting a model:

- review validation strategy
- inspect PR-AUC, recall, precision, and threshold report
- compare against the current champion model
- check drift report
- document threshold and model version
- retain prior model artifact for rollback
