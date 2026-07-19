# Deployment Options

## Local Docker Compose

Best for portfolio demo and local integration testing.

```cmd
scripts\full_demo.bat
```

## AWS ECS/Fargate

Good first production target:

- Push API/frontend images to ECR.
- Run FastAPI on ECS Fargate.
- Serve React from S3 + CloudFront or nginx container.
- Connect to RDS PostgreSQL, MSK, and S3.

## Kubernetes

Best when a team already operates Kubernetes:

- EKS, AKS, or GKE
- Horizontal pod autoscaling
- Ingress with TLS
- External secrets operator
- Managed PostgreSQL and Kafka outside the cluster

## Cloud Run / Container Apps

Good for simpler container operations:

- GCP Cloud Run or Azure Container Apps
- Autoscaling HTTP API
- Managed secrets
- Managed database and streaming integrations

## Recommendation

For this project, use:

```text
Local demo -> ECS/Fargate or Cloud Run -> Kubernetes only if platform maturity exists
```
