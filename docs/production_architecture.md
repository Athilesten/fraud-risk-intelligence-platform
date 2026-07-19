# Production Architecture

## Purpose

The platform scores financial transactions for fraud risk, combines ML probability with an explainable rule engine, stores prediction audit logs, and exposes monitoring data for operations.

## System Flow

```text
React Frontend -> FastAPI -> ML Model + Rule Engine -> PostgreSQL -> Prometheus/Grafana
Kafka Raw Topic -> Kafka Scoring Consumer -> FastAPI -> Kafka Scored Topic -> PySpark -> Delta Lake
```

## Components

| Component | Responsibility |
|---|---|
| React frontend | Main product UI for overview, prediction, batch scoring, logs, monitoring, and architecture |
| FastAPI | Scoring API, API key authentication, validation, structured request handling |
| ML model | Fraud probability and ML risk level |
| Rule engine | Explainable business risk score, triggered rules, and final decision support |
| PostgreSQL | Prediction audit log storage |
| Kafka | Raw and scored transaction event streams |
| PySpark | Structured Streaming transformations |
| Delta Lake | Bronze, silver, and gold analytical tables |
| Prometheus | Scrapes FastAPI metrics from `/metrics` |
| Grafana | Advanced monitoring dashboard |
| Streamlit | Optional internal analyst dashboard |

## Public Endpoints

- `GET /`
- `GET /health`
- `GET /metrics`
- `GET /docs`

## Protected Endpoints

All protected endpoints require `X-API-Key`.

- `POST /predict`
- `POST /predict_batch`
- `GET /prediction_logs?limit=20`
- `GET /monitoring/metrics`
- `GET /streaming/status`
- `GET /streaming/recent-scored`
- `GET /datalake/summary`

## Deployment Ports

| Service | Port |
|---|---|
| React frontend | `3001` |
| FastAPI | `8000` |
| Streamlit internal dashboard | `8501` |
| Prometheus | `9090` |
| Grafana | `3000` |
| Kafka UI | `8080` |

## Production Backlog

- Replace local API key authentication with OAuth/OIDC or API gateway auth
- Add Alembic migrations for database schema changes
- Add role-based access control for analyst workflows
- Add CI container scanning and dependency vulnerability checks
- Add persisted metrics backend for long-term trend analysis
