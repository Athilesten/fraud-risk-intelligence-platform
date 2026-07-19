terraform {
  required_version = ">= 1.6.0"
}

# Azure production blueprint:
# - React: Azure Static Web Apps or App Service
# - FastAPI: Azure Container Apps or AKS
# - PostgreSQL: Azure Database for PostgreSQL
# - Kafka: Confluent Cloud or Event Hubs Kafka endpoint
# - Data Lake: ADLS Gen2
# - Spark: Azure Databricks or Synapse Spark
# - Secrets: Azure Key Vault

variable "project_name" {
  type    = string
  default = "fraud-risk-platform"
}

output "blueprint" {
  value = "Azure Container Apps/AKS + Azure PostgreSQL + ADLS Gen2 + Databricks + Key Vault"
}
