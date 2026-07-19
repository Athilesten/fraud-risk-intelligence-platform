# Cloud Production Plan

This project runs locally for portfolio and interview demos. A real enterprise deployment should keep the same architecture and replace local services with managed, secure infrastructure.

## Target Cloud Architecture

```text
React CDN -> API Gateway/Load Balancer -> FastAPI Scoring Service
FastAPI -> Managed PostgreSQL
Kafka Producer/Consumers -> Managed Kafka
Spark Jobs -> Managed Spark
Delta Lake -> Cloud Object Storage
Prometheus/Grafana -> Managed Observability
Secrets -> Cloud Secret Manager
```

## AWS Option

- React frontend: S3 + CloudFront or Amplify
- FastAPI: ECS Fargate, EKS, or App Runner
- PostgreSQL: Amazon RDS PostgreSQL
- Kafka: MSK or Confluent Cloud
- Spark: EMR Serverless or AWS Glue
- Data lake: S3 with Delta Lake table paths
- Secrets: AWS Secrets Manager
- Monitoring: Amazon Managed Prometheus + Grafana Cloud/Amazon Managed Grafana

## GCP Option

- React frontend: Cloud Storage + Cloud CDN or Firebase Hosting
- FastAPI: Cloud Run or GKE
- PostgreSQL: Cloud SQL for PostgreSQL
- Kafka: Confluent Cloud
- Spark: Dataproc Serverless
- Data lake: Google Cloud Storage
- Secrets: Secret Manager
- Monitoring: Cloud Monitoring + Grafana Cloud

## Azure Option

- React frontend: Azure Static Web Apps or Storage Static Website + CDN
- FastAPI: Azure Container Apps or AKS
- PostgreSQL: Azure Database for PostgreSQL
- Kafka: Confluent Cloud or Event Hubs Kafka endpoint
- Spark: Azure Databricks or Synapse Spark
- Data lake: ADLS Gen2
- Secrets: Azure Key Vault
- Monitoring: Azure Monitor + Grafana

## Production Security Requirements

- HTTPS everywhere
- OAuth2/OIDC login through Auth0, Azure AD, Cognito, or another identity provider
- Role-based access control for admin, analyst, and viewer users
- Secrets stored in a managed secret store, never in `.env`
- Private networking for database, Kafka, and model services
- Audit logs retained according to compliance policy
- Rate limiting and request-size limits on public APIs

## ML Platform Requirements

- MLflow model registry with versioned models
- Model approval workflow before production promotion
- Offline evaluation report for every model version
- Drift checks for transaction amount, type distribution, and fraud score distribution
- Scheduled retraining pipeline
- Rollback path to previous approved model

## Reliability Requirements

- Multiple API replicas behind a load balancer
- Health checks and readiness checks
- Kafka consumer retry and dead-letter policy
- Database backups and point-in-time recovery
- Load testing before production release
- Alerting for API errors, latency, high-risk spikes, and consumer lag

## What Remains Outside This Local Demo

The local project proves architecture, integration, and demo behavior. Real enterprise production still needs cloud infrastructure, SSO/RBAC, managed secrets, high availability, compliance review, load testing, and a governed model-release process.
