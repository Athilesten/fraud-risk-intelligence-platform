# Industry Architecture

## Online Fraud Scoring Layer

```text
React SaaS Frontend -> FastAPI Scoring API -> Feature Engineering -> ML Model -> Rule Engine -> PostgreSQL Audit Logs
```

This layer is used for interactive single prediction, batch CSV scoring, audit logs, and monitoring shown in the React product UI.

## Streaming Fraud Layer

```text
PaySim / IEEE-CIS / Simulator -> transactions.raw -> Kafka Scoring Consumer -> FastAPI /predict -> transactions.scored
```

Kafka separates ingestion from scoring. The scoring consumer calls the same FastAPI `/predict` endpoint as the frontend, so online and streaming decisions use one scoring contract.

## Lakehouse Layer

```text
transactions.raw -> PySpark Structured Streaming -> Delta Bronze -> Delta Silver -> Delta Gold
transactions.scored -> PySpark Structured Streaming -> Gold Scored Decisions
```

Bronze stores raw canonical events. Silver stores cleaned and feature-engineered transactions. Gold stores analytics summaries and scored fraud decisions.

## Observability Layer

```text
FastAPI /metrics -> Prometheus -> Grafana
```

Grafana is provisioned with a fraud platform dashboard that uses real Prometheus metrics.

## Engineering Layer

- Unit tests for fraud rules, feature engineering, schema validation, API auth, and data lake summaries
- Docker Compose app and streaming stacks
- Alembic migration path for PostgreSQL
- GitHub Actions CI for backend, frontend, and Compose validation
- Windows run scripts and runbook
