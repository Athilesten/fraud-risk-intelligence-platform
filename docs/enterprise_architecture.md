# Enterprise Architecture

This platform has two layers:

1. A working local demo using Docker Compose.
2. An enterprise production blueprint using managed cloud services.

## Logical Flow

```text
React SaaS UI
  -> FastAPI Scoring API
  -> ML Model + Rule Engine
  -> PostgreSQL Audit Logs
  -> Prometheus/Grafana Observability

Kafka Raw Topic
  -> Scoring Consumer
  -> FastAPI /predict
  -> Kafka Scored Topic
  -> Spark/Delta Lake Bronze/Silver/Gold
```

## AWS Option

| Capability | AWS Service |
|---|---|
| Frontend | S3 + CloudFront or ECS/Fargate |
| API | ECS Fargate, EKS, or Lambda container |
| PostgreSQL | Amazon RDS PostgreSQL |
| Kafka | Amazon MSK |
| Data lake | Amazon S3 |
| Spark | EMR, Glue, or Databricks |
| Secrets | AWS Secrets Manager |
| Monitoring | CloudWatch + Prometheus/Grafana |
| Model registry | MLflow on ECS/S3/RDS or SageMaker Model Registry |
| CI/CD | GitHub Actions -> ECR -> ECS/EKS |

## Azure Option

| Capability | Azure Service |
|---|---|
| Frontend | Azure Static Web Apps or App Service |
| API | Azure Container Apps or AKS |
| PostgreSQL | Azure Database for PostgreSQL |
| Kafka | Confluent Cloud or Event Hubs Kafka API |
| Data lake | ADLS Gen2 |
| Spark | Azure Databricks or Synapse |
| Secrets | Azure Key Vault |
| Monitoring | Azure Monitor + Grafana |
| Model registry | MLflow or Azure ML Registry |

## GCP Option

| Capability | GCP Service |
|---|---|
| Frontend | Cloud Storage + CDN or Cloud Run |
| API | Cloud Run or GKE |
| PostgreSQL | Cloud SQL PostgreSQL |
| Kafka | Confluent Cloud or Pub/Sub alternative |
| Data lake | GCS |
| Spark | Dataproc or Dataflow |
| Secrets | Secret Manager |
| Monitoring | Cloud Monitoring + Grafana |
| Model registry | Vertex AI Model Registry or MLflow |

## Recommended Path

For this project, the cleanest production path is:

```text
React on CDN
FastAPI on container platform
Managed PostgreSQL
Managed Kafka
Cloud object-storage data lake
Managed Spark
MLflow or cloud model registry
Centralized monitoring and alerting
```
