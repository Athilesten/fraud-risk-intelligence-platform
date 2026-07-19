# Interview Explanation

## One-Minute Pitch

This is an industry-style fraud risk intelligence platform. A React product frontend lets users score single transactions, upload CSV batches, inspect PostgreSQL prediction logs, view monitoring metrics, and inspect local Kafka/Spark/Delta pipeline status. The FastAPI backend validates requests, authenticates protected endpoints with an API key, runs an ML fraud model, applies a rule engine, logs predictions to PostgreSQL, and exposes metrics for Prometheus and Grafana.

## How To Explain The Architecture

```text
React Frontend -> FastAPI -> ML Model + Rule Engine -> PostgreSQL -> Prometheus/Grafana
```

React is the main product interface. FastAPI is the backend scoring service. Kafka carries raw and scored transaction events. PySpark Structured Streaming writes bronze, silver, and gold Delta Lake tables. PostgreSQL stores the operational audit trail. Prometheus and Grafana provide production-style observability.

## Demo Flow

1. Open `http://localhost:3001`.
2. Show the overview and system status card.
3. Run the default transaction in the Fraud Prediction section.
4. Explain fraud probability, risk level, rule score, final decision, triggered rules, and top features.
5. Upload `examples/sample_batch_transactions.csv` in Batch Prediction.
6. Show high, medium, low risk counts and the real result table.
7. Load Prediction Logs and explain that the data comes from PostgreSQL.
8. Load Monitoring and explain endpoint-level request count, errors, and latency.
9. Start Kafka, create topics, run the producer, and run the scoring consumer.
10. Refresh Big Data Pipeline and show recent Kafka-scored transactions.
11. Open Grafana as the advanced monitoring surface.

## Key Talking Points

- This is a platform project, not just a notebook.
- React is the customer-facing product UI.
- FastAPI exposes a clean backend contract.
- PostgreSQL gives traceability for fraud decisions.
- The rule engine makes decisions explainable to non-ML stakeholders.
- Monitoring is included through both API metrics and Prometheus/Grafana.
- Kafka, PySpark, and Delta Lake demonstrate the scalable big-data extension.
- Streamlit is kept only as an internal analyst dashboard.

## Honest Limitations

- The local API key is for demo only and should be replaced for production.
- The database schema is created directly at startup; production should use migrations.
- Model explanation currently falls back to feature importance if SHAP fails for the loaded model.
- Grafana dashboards can be customized further for a polished production observability story.
