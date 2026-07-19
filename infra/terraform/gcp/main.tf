terraform {
  required_version = ">= 1.6.0"
}

# GCP production blueprint:
# - React: Cloud Storage + CDN or Cloud Run
# - FastAPI: Cloud Run or GKE
# - PostgreSQL: Cloud SQL PostgreSQL
# - Kafka: Confluent Cloud or Pub/Sub alternative
# - Data Lake: GCS
# - Spark: Dataproc Serverless
# - Secrets: Secret Manager
# - Model registry: Vertex AI Model Registry or MLflow

variable "project_name" {
  type    = string
  default = "fraud-risk-platform"
}

output "blueprint" {
  value = "Cloud Run/GKE + Cloud SQL + GCS + Dataproc + Secret Manager"
}
