# AWS Terraform Blueprint

This folder is a safe production blueprint for the fraud risk platform. It does not include real credentials and should not be auto-applied from CI.

## Intended Mapping

- React frontend: S3 + CloudFront or ECS/Fargate
- FastAPI: ECS Fargate, EKS, or Lambda container
- PostgreSQL: Amazon RDS PostgreSQL
- Kafka: Amazon MSK
- Data lake: S3 with Delta Lake paths
- Spark: EMR, Glue, or Databricks
- Secrets: AWS Secrets Manager
- Monitoring: CloudWatch plus Prometheus/Grafana
- CI/CD: GitHub Actions -> ECR -> ECS/EKS

## Safe Usage

```bash
terraform init
terraform validate
terraform plan
```

Do not run `terraform apply` until networking, IAM, cost controls, and security review are completed.
