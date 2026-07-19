# Real-Time Fraud Detection and Risk Intelligence Platform

An industry-style fintech fraud risk platform with a polished React product UI, FastAPI ML scoring backend, rule engine, PostgreSQL audit logging, Kafka streaming ingestion, PySpark Structured Streaming, local Delta Lake bronze/silver/gold tables, Docker deployment, Prometheus/Grafana monitoring, and enterprise cloud-production blueprint.

This is not only a machine learning notebook and not only a Streamlit dashboard. The React website is the main product interface. Streamlit remains available as an internal analyst dashboard.

## Core Capabilities

- Single transaction fraud scoring through FastAPI
- Batch CSV fraud scoring with required-column validation
- ML fraud probability, risk level, rule score, final decision, and triggered rules
- Model explanation/top features when the explanation service returns them
- PostgreSQL prediction audit logs
- API metrics for request count, errors, average latency, max latency, and endpoint breakdown
- Kafka raw/scored transaction topics
- PySpark Structured Streaming pipelines
- Local Delta Lake bronze/silver/gold architecture
- Optional local JWT login flow plus service API key support
- Alembic migration path for PostgreSQL
- Prometheus metrics endpoint and Grafana monitoring
- Docker Compose stack for local presentation
- RBAC permission model for demo JWT users and service API keys
- Locust load-testing workload
- Cloud, security, compliance, model governance, Kubernetes, and Terraform blueprints

## Architecture

```text
React Frontend -> FastAPI -> ML Model + Rule Engine -> PostgreSQL -> Prometheus/Grafana
Kafka Raw Topic -> Kafka Scoring Consumer -> FastAPI -> Kafka Scored Topic -> PySpark -> Delta Lake
```

## Documentation

- [Big Data Streaming Architecture](docs/big_data_streaming_architecture.md)
- [Runbook](docs/runbook.md)
- [Interview Demo Script](docs/interview_demo_script.md)
- [Industry Architecture](docs/industry_architecture.md)
- [Enterprise Architecture](docs/enterprise_architecture.md)
- [Cloud Production Plan](docs/cloud_production_plan.md)
- [Deployment Options](docs/deployment_options.md)
- [Managed Kafka Plan](docs/managed_kafka_plan.md)
- [Managed PostgreSQL Plan](docs/managed_postgres_plan.md)
- [Cloud Data Lake Plan](docs/cloud_datalake_plan.md)
- [Auth And RBAC Plan](docs/auth_rbac_plan.md)
- [Secrets Management Plan](docs/secrets_management_plan.md)
- [Model Governance Plan](docs/model_governance_plan.md)
- [Security Compliance Review](docs/security_compliance_review.md)
- [CI/CD Plan](docs/ci_cd_plan.md)
- [Observability Plan](docs/observability_plan.md)
- [Load Testing Report Template](docs/load_testing_report_template.md)
- [Alerting Strategy](docs/alerting_strategy.md)
- [Limitations And Future Scope](docs/limitations_and_future_scope.md)
- [Production Architecture](docs/production_architecture.md)
- [Interview Explanation](docs/interview_explanation.md)

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Axios, Recharts |
| Backend | FastAPI, Pydantic, API key authentication |
| ML | Scikit-learn/XGBoost model artifacts, feature engineering, rule engine |
| Operational Storage | PostgreSQL prediction audit logs |
| Streaming | Kafka, kafka-python |
| Data Lake | PySpark Structured Streaming, Delta Lake |
| Monitoring | Prometheus metrics, Grafana dashboard |
| Internal Dashboard | Streamlit |
| Deployment | Docker Compose, nginx frontend container |
| Enterprise Blueprint | Terraform, Kubernetes manifests, cloud production docs |
| Load Testing | Locust |

## Environment

Use Python 3.11 for the local ML and Spark environment. Python 3.13 can force older ML packages such as NumPy 1.x to build from source on Windows.

Copy `.env.example` to `.env` for local development.

Local demo API key:

```text
dev_fraud_api_key_123
```

Protected API requests use:

```text
X-API-Key: dev_fraud_api_key_123
```

Important local variables:

```text
VITE_API_BASE_URL=http://localhost:8000
VITE_API_KEY=dev_fraud_api_key_123
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_RAW_TOPIC=transactions.raw
KAFKA_SCORED_TOPIC=transactions.scored
KAFKA_ERROR_TOPIC=transactions.errors
DATA_LAKE_PATH=data/delta
JWT_SECRET_KEY=local_demo_jwt_secret_change_me
DEMO_ADMIN_EMAIL=admin@fraud.local
DEMO_ADMIN_PASSWORD=admin123
DEMO_ADMIN_ROLE=admin
```

## Local Working Demo

The local demo requires no cloud credentials.

```cmd
cd D:\fraud-risk-intelligence-platform
py -3.11 -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements-ci.txt
pip install -r streaming-requirements.txt
cd frontend
npm install
npm run build
cd ..
scripts\validate_project.bat
scripts\full_demo.bat
```

## Run App Stack

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\start_app_stack.bat
```

## Run Streaming Stack

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\start_streaming_stack.bat
timeout /t 60
scripts\create_kafka_topics.bat
```

If `data/raw/paysim.csv` is missing:

```cmd
.\venv\Scripts\python.exe scripts\generate_sample_paysim.py --rows 200
```

## Streaming Demo Commands

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\run_kafka_demo.bat
```

Optional Spark pipelines:

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\run_spark_delta_demo.bat
```

Full local interview demo after dependencies are installed:

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\full_demo.bat
```

## Database Migrations

The app still creates the prediction table at startup as a local fallback. The professional migration path is Alembic:

```cmd
cd D:\fraud-risk-intelligence-platform
set DATABASE_URL=postgresql://fraud_user:fraud_password@localhost:5433/fraud_db
.\venv\Scripts\alembic.exe upgrade head
```

## Service URLs

| Service | URL |
|---|---|
| React product frontend | http://localhost:3001 |
| FastAPI backend | http://localhost:8000 |
| FastAPI docs | http://localhost:8000/docs |
| Streamlit internal dashboard | http://localhost:8501 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| Kafka UI | http://localhost:8080 |

## API Endpoints

Public:

- `GET /`
- `GET /health`
- `GET /metrics`
- `GET /docs`
- `POST /auth/login`

Protected:

- `GET /auth/me`
- `POST /predict`
- `POST /predict_batch`
- `GET /prediction_logs?limit=20`
- `GET /monitoring/metrics`
- `GET /streaming/status`
- `GET /streaming/recent-scored`
- `GET /datalake/summary`

## Batch CSV Columns

The frontend validates these required columns before scoring:

```text
step,type,amount,oldbalanceOrg,newbalanceOrig,oldbalanceDest,newbalanceDest,isFlaggedFraud
```

Sample file:

```text
examples/sample_batch_transactions.csv
```

## Interview Positioning

Present this as an industry-style fraud risk intelligence platform with React SaaS frontend, FastAPI ML backend, rule engine, PostgreSQL audit logs, Kafka real-time ingestion, PySpark Structured Streaming, Delta Lake bronze/silver/gold architecture, Dockerized local deployment, and Prometheus/Grafana monitoring.

Do not overclaim it as a deployed bank production system. It is a production-style local implementation designed for portfolio and interview demonstration.

## Validation Commands

```cmd
cd D:\fraud-risk-intelligence-platform\frontend
npm install
npm run build

cd D:\fraud-risk-intelligence-platform
python -m py_compile api\main.py
python -m py_compile streaming\kafka_producer.py
python -m py_compile streaming\kafka_scoring_consumer.py
python -m py_compile streaming\spark_streaming_delta_pipeline.py
python -m py_compile streaming\spark_scored_delta_pipeline.py
docker compose -f docker-compose.app.yml config
docker compose -f docker-compose.streaming.yml config
scripts\validate_project.bat
```

## Load Testing

Load testing is optional and is not required by CI.

```cmd
cd D:\fraud-risk-intelligence-platform
call venv\Scripts\activate.bat
pip install locust
locust -f load_tests\locustfile.py --host=http://localhost:8000
```

Headless run:

```cmd
locust -f load_tests\locustfile.py --host=http://localhost:8000 --users 20 --spawn-rate 5 --run-time 2m --headless
```

## Enterprise Production Blueprint

The repository includes safe, non-credentialed templates for:

- AWS/Azure/GCP production architecture
- Managed Kafka
- Managed PostgreSQL
- Cloud data lake
- OAuth/SSO and RBAC
- Secret manager integration
- Kubernetes deployment starting point
- Terraform structure
- Model governance and compliance review

These assets are for planning and interview architecture explanation. They are not a fully deployed bank production system.
