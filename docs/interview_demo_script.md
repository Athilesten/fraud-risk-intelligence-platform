# Interview Demo Script

## Problem

Fintech and payment companies need to identify suspicious transactions quickly, explain why a transaction is risky, store decisions for audit, and monitor system health.

## Architecture

```text
React Frontend -> FastAPI -> ML Model + Rule Engine -> PostgreSQL Logs -> Monitoring
Kafka Raw Topic -> Kafka Scoring Consumer -> FastAPI -> Kafka Scored Topic -> PySpark -> Delta Lake
```

## Demo Flow

1. Open `http://localhost:3001`.
2. Show the React SaaS frontend and system status.
3. Run a single fraud prediction.
4. Explain fraud probability, risk level, rule score, final decision, triggered rules, and top features.
5. Upload `examples/sample_batch_transactions.csv`.
6. Load PostgreSQL prediction logs.
7. Load API monitoring metrics.
8. Start Kafka and create topics.
9. Run the producer for 20 records.
10. Run the scoring consumer for 20 records.
11. Refresh Big Data Pipeline in React and show recent Kafka-scored transactions.
12. If Spark is running, show Delta Lake counts and transaction type distribution.

## Why Kafka

Kafka represents the real-time transaction ingestion layer. In industry, payment systems publish transaction events to Kafka so downstream services can score, monitor, and analyze them independently.

## Why Spark

PySpark Structured Streaming is used for large-scale stream processing. It can continuously transform raw transaction events into analytical datasets.

## Why Delta Lake

Delta Lake gives a bronze/silver/gold data lake architecture:

- Bronze: raw ingested events
- Silver: cleaned and feature-engineered transactions
- Gold: aggregated fraud-risk analytics and scored decisions

## Why PostgreSQL

PostgreSQL is the operational audit database for predictions shown in the product UI. It is not a replacement for the data lake.

## Why FastAPI

FastAPI is the scoring service. Both React and Kafka scoring consumer call the same `/predict` endpoint, which keeps model serving consistent.

## Why React

React is the main product interface for client-facing scoring, logs, monitoring, and big-data pipeline status.

## Production-Style Elements

- Dockerized local deployment
- Protected scoring endpoints
- PostgreSQL operational logs
- Prometheus/Grafana monitoring
- Kafka streaming topics
- PySpark Structured Streaming
- Delta Lake bronze/silver/gold architecture
- Clear separation between online serving and offline analytics

## Honest Limitations

This is a production-style local implementation, not a deployed bank production system. Future production work would include Kubernetes, cloud object storage, HTTPS, RBAC, secret manager, CI/CD deployment, load testing, schema registry, and compliance controls.
