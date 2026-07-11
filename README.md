# Real-Time Fraud Detection and Risk Intelligence Platform

## Project Overview

This project is an end-to-end fraud detection and risk intelligence platform built for detecting suspicious financial transactions using machine learning, rule-based risk scoring, batch prediction, real-time simulation, Kafka streaming, and analyst dashboards.

The system supports:
- Single transaction fraud prediction
- Batch CSV fraud scoring
- Fraud alert logging
- Rule-based risk engine
- SHAP/feature explanation
- Real-time transaction simulation
- Kafka-based streaming pipeline
- MLflow experiment tracking
- Streamlit dashboard for analysts

---

## Business Problem

Financial institutions, fintech companies, and payment platforms need to identify suspicious transactions quickly. Fraud datasets are highly imbalanced, so accuracy alone is not suitable. This project focuses on fraud probability, PR-AUC, recall, rule explanations, and real-time alert monitoring.

---

## Tech Stack

| Area | Tools |
|---|---|
| Programming | Python |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn, XGBoost |
| Model Tracking | MLflow |
| Explainability | SHAP / Feature Importance |
| API | FastAPI |
| Dashboard | Streamlit, Plotly |
| Streaming | Kafka |
| Container | Docker |
| Storage | CSV logs |

---

## Project Architecture

```text
Transaction Input / CSV / Simulator / Kafka Producer
              ↓
        FastAPI Scoring API
              ↓
    ML Model + Rule Engine
              ↓
Fraud Probability + Rule Score + Final Decision
              ↓
 Streamlit Dashboard + Alert Logs

 fraud-risk-intelligence-platform/
│
├── api/
│   └── main.py
│
├── dashboard/
│   └── app.py
│
├── data/
│   ├── raw/
│   │   └── paysim.csv
│   └── processed/
│       ├── fraud_alerts.csv
│       ├── batch_predictions.csv
│       ├── realtime_simulation_log.csv
│       └── kafka_scored_transactions.csv
│
├── models/
│   ├── fraud_model.pkl
│   └── label_encoder.pkl
│
├── src/
│   ├── data_preprocessing.py
│   ├── feature_engineering.py
│   ├── train_model.py
│   ├── train_model_mlflow.py
│   ├── train_model_compare_mlflow.py
│   ├── predict.py
│   ├── explain.py
│   └── rules_engine.py
│
├── streaming/
│   ├── transaction_simulator.py
│   ├── kafka_producer.py
│   └── kafka_consumer.py
│
├── docker-compose.yml
├── requirements.txt
└── README.md

Dataset

This project uses PaySim-style transaction data.

Required columns:

step, type, amount, oldbalanceOrg, newbalanceOrig,
oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud

Target column:

isFraud


Model Training

Train basic model:

python src/train_model.py

Train model with MLflow tracking:

python src/train_model_mlflow.py

Compare Random Forest and XGBoost automatically:

python src/train_model_compare_mlflow.py

The best model is selected using:

Selection Score = 70% PR-AUC + 30% Recall

The best model is saved as:

models/fraud_model.pkl

Run FastAPI
uvicorn api.main:app --reload

API docs:

http://127.0.0.1:8000/docs


Run Streamlit Dashboard
streamlit run dashboard/app.py

Dashboard URL:

http://localhost:8501

Run Real-Time Simulator
python streaming/transaction_simulator.py

This generates live-style transactions and saves scored results to:

data/processed/realtime_simulation_log.csv

Run Kafka Streaming

Start Kafka:

docker compose up -d

Start FastAPI:

uvicorn api.main:app --reload

Start Kafka consumer:

python streaming/kafka_consumer.py

Start Kafka producer:

python streaming/kafka_producer.py

Kafka scored results are saved to:

data/processed/kafka_scored_transactions.csv

Stop Kafka:

docker compose down


MLflow UI

Run:

mlflow ui --backend-store-uri sqlite:///mlflow.db

Open:

http://127.0.0.1:5000
Evaluation Metrics

This project uses:

ROC-AUC
PR-AUC
Precision
Recall
F1-score
Rule risk score
Final decision count
Batch prediction risk distribution
Kafka streaming decision distribution

Fraud detection is imbalanced, so PR-AUC and recall are more important than accuracy.

Rule Engine

The rule engine checks:

High value transaction
Sender balance becoming zero
Risky transaction type
System flagged fraud
Sender balance mismatch
Receiver balance mismatch

The final decision is:

APPROVE
MANUAL REVIEW
BLOCK / MANUAL REVIEW
Dashboard Features

The Streamlit dashboard supports:

Single transaction prediction
Fraud probability
Rule risk score
Triggered fraud rules
Final decision
Model explanation
Batch CSV prediction
Batch prediction history
Real-time simulator monitoring
Kafka streaming monitoring
CSV download
