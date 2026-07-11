\# Production Architecture



\## Project Name



Real-Time Fraud Detection and Risk Intelligence Platform



\## High-Level Architecture



```mermaid

flowchart TD



&#x20;   A\[Transaction Source / User Input] --> B\[Streamlit Risk Dashboard]

&#x20;   A --> C\[Kafka Producer]



&#x20;   C --> D\[Kafka Topic: transactions]

&#x20;   D --> E\[Spark Structured Streaming]



&#x20;   E --> F\[Delta Lake Raw Transactions]

&#x20;   E --> G\[Delta Lake Curated Transactions]



&#x20;   B --> H\[FastAPI Fraud Scoring Service]



&#x20;   H --> I\[Feature Engineering]

&#x20;   I --> J\[ML Model: RandomForest / XGBoost]

&#x20;   I --> K\[Rule-Based Risk Engine]



&#x20;   J --> L\[Fraud Probability]

&#x20;   K --> M\[Rule Risk Score]



&#x20;   L --> N\[Final Risk Decision]

&#x20;   M --> N



&#x20;   N --> O\[SHAP / Feature Importance Explanation]

&#x20;   N --> P\[PostgreSQL Prediction Logs]



&#x20;   P --> B



&#x20;   H --> Q\[Prometheus Metrics Endpoint /metrics]

&#x20;   Q --> R\[Prometheus]

&#x20;   R --> S\[Grafana Monitoring Dashboard]



&#x20;   T\[Airflow Retraining DAG] --> U\[Model Training Pipeline]

&#x20;   U --> V\[MLflow Experiment Tracking]

&#x20;   U --> W\[Updated Model Artifacts]



&#x20;   W --> H

```



\## Component Explanation



\### 1. Transaction Source



Transactions can come from:



\- Manual Streamlit input

\- Batch CSV upload

\- Kafka real-time producer

\- Simulated transaction stream



\### 2. FastAPI Fraud Scoring Service



FastAPI acts as the production API layer.



Responsibilities:



\- Accept transaction input

\- Validate request schema using Pydantic

\- Check API key authentication

\- Call ML prediction pipeline

\- Call rule-based fraud engine

\- Generate explanation

\- Save prediction logs into PostgreSQL

\- Expose monitoring metrics



Protected endpoints:



\- `POST /predict`

\- `POST /predict\_batch`

\- `GET /prediction\_logs`

\- `GET /monitoring/metrics`



Public endpoints:



\- `GET /`

\- `GET /health`

\- `GET /metrics`



\### 3. Machine Learning Layer



The ML layer includes:



\- Data preprocessing

\- Feature engineering

\- Label encoding

\- RandomForest model

\- XGBoost model comparison

\- Fraud probability prediction

\- Risk-level classification



The model outputs:



\- Fraud probability

\- Risk level

\- Alert message

\- Final decision



\### 4. Rule-Based Risk Engine



The rule engine adds business logic on top of ML.



Example rules:



\- High-value transaction

\- Sender balance becomes zero

\- Risky transaction type

\- Receiver balance mismatch

\- Existing flagged fraud indicator



This improves explainability and production trust.



\### 5. PostgreSQL Prediction Logging



Every prediction is saved into PostgreSQL.



Stored fields include:



\- Transaction details

\- Fraud probability

\- ML risk level

\- Rule risk level

\- Triggered rules

\- Final decision

\- Explanation JSON

\- Timestamp



This makes the system auditable.



\### 6. Streamlit Risk Intelligence Dashboard



The dashboard provides:



\- Single transaction scoring

\- Batch CSV scoring

\- PostgreSQL prediction logs

\- API monitoring metrics

\- Risk-level visualizations

\- Fraud decision monitoring



\### 7. Kafka Streaming Layer



Kafka is used for real-time transaction streaming.



Flow:



```text

Producer → Kafka topic → Consumer / Spark Streaming

```



\### 8. Spark Structured Streaming + Delta Lake



Spark processes streaming transactions and stores data in:



\- Raw Delta table

\- Curated Delta table



This gives the project a Big Data architecture.



\### 9. MLflow



MLflow tracks:



\- Model experiments

\- Metrics

\- Parameters

\- Model comparison

\- Best model selection



\### 10. Airflow



Airflow automates retraining.



DAG flow:



```text

Validate project structure

&#x20;       ↓

Validate dataset

&#x20;       ↓

Run retraining pipeline

&#x20;       ↓

Validate model artifacts

```



\### 11. Prometheus + Grafana



FastAPI exposes Prometheus metrics at:



```text

/metrics

```



Prometheus collects:



\- Request count

\- Request latency

\- Prediction count

\- Fraud probability distribution

\- Risk-level counters



Grafana visualizes:



\- Total API requests

\- Request rate

\- Average latency

\- 95th percentile latency

\- Total fraud predictions

\- Predictions by risk level

\- Predictions by final decision



\## Production-Style Features



This project includes:



\- Dockerized API and dashboard

\- PostgreSQL database

\- API key authentication

\- Structured JSON logging

\- Request latency monitoring

\- Prometheus metrics

\- Grafana dashboard

\- MLflow tracking

\- Airflow retraining

\- Kafka streaming

\- Spark + Delta Lake

\- Pytest unit tests

\- GitHub Actions CI workflow



\## Limitations



This is a production-style portfolio project.



A real enterprise deployment would additionally need:



\- Cloud deployment

\- HTTPS

\- Load balancer

\- Kubernetes

\- Secret manager

\- Role-based access control

\- Database backup strategy

\- Model approval workflow

\- Data privacy and compliance review



