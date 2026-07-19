# Big Data Streaming Architecture

## Current Online Scoring Flow

```text
React Frontend -> FastAPI -> Feature Engineering -> ML Model + Rule Engine -> PostgreSQL Logs -> React Logs / Monitoring
```

This is the main working product flow. React calls FastAPI, FastAPI validates and scores the transaction, the model returns fraud probability, the rule engine returns explainable risk signals, and PostgreSQL stores prediction audit logs.

## Kafka Streaming Flow

```text
PaySim / IEEE Dataset -> Kafka Producer -> transactions.raw
```

`streaming/kafka_producer.py` reads local dataset records, normalizes them into the canonical schema, adds `event_id`, `event_time`, and `source_dataset`, then publishes JSON events to Kafka topic `transactions.raw`.

## Real-Time Scoring Flow

```text
transactions.raw -> Kafka Scoring Consumer -> FastAPI /predict -> PostgreSQL Logs -> transactions.scored
```

`streaming/kafka_scoring_consumer.py` consumes raw events, calls FastAPI `/predict` using `X-API-Key`, lets FastAPI write PostgreSQL logs, and publishes enriched events to `transactions.scored`.

## Spark + Delta Lake Flow

```text
transactions.raw -> PySpark Structured Streaming -> Bronze -> Silver -> Gold
transactions.scored -> PySpark Structured Streaming -> Gold Scored Decisions
```

Bronze stores raw canonical events.
Silver stores cleaned transactions and engineered risk features.
Gold stores fraud-risk analytics and scored decisions.

Local Delta Lake paths:

```text
data/delta/bronze/transactions_raw
data/delta/silver/transactions_features
data/delta/gold/fraud_risk_summary
data/delta/gold/scored_fraud_decisions
```

## PostgreSQL vs Data Lake

PostgreSQL is the operational audit database. It stores prediction results used by the React product UI and analyst workflows.

Delta Lake is the analytical storage layer. It stores raw and transformed event streams for offline analytics, model training, reporting, and future large-scale fraud intelligence.

## Monitoring

FastAPI exposes Prometheus metrics at `/metrics`. Prometheus scrapes the API, and Grafana provides production-style monitoring dashboards.

## Dataset Strategy

PaySim is used for streaming demos because it already matches payment fraud features such as balances, transaction type, amount, and fraud labels.

IEEE-CIS is supported as an offline analytics/model-training extension. Because IEEE-CIS does not provide the same PaySim balance fields, the loader maps important fields into the canonical schema and uses safe zero defaults for missing balance columns. Those defaults are documented and should not be treated as real PaySim-style fraud logic.
