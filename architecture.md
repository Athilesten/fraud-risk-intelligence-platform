# Architecture Note

## 1. Data Sources

The platform accepts transactions from three sources:

1. Manual single transaction input
2. Batch CSV upload
3. Real-time simulator / Kafka producer

---

## 2. API Layer

FastAPI exposes two main endpoints:

```text
POST /predict
POST /predict_batch


. ML Prediction Layer

The prediction layer performs:

Data validation
Transaction type encoding
Feature engineering
ML model prediction
Rule engine evaluation
Final decision generation
Explanation generation
4. Rule Engine

The rule engine provides explainable risk checks. It does not replace the ML model. It supports the ML model by giving transparent fraud indicators.

5. Storage Layer

The project stores outputs in CSV format:

fraud_alerts.csv
batch_predictions.csv
realtime_simulation_log.csv
kafka_scored_transactions.csv
6. Dashboard Layer

Streamlit dashboard shows:

Current prediction
Alert history
Batch scoring results
Real-time logs
Kafka scored transactions
Risk charts
Downloadable reports
7. MLOps Layer

MLflow tracks:

Model name
Model parameters
ROC-AUC
PR-AUC
Precision
Recall
F1-score
Selection score
Model artifacts
8. Streaming Layer

Kafka is used for event streaming.

Kafka Producer → transactions topic → Kafka Consumer → FastAPI → scored CSV log

This simulates how payment events can be processed in near real time.