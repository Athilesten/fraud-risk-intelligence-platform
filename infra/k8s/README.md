# Kubernetes Blueprint

These manifests are optional production-starting templates. They are not required for the local Docker Compose demo.

## Recommended Production Changes Before Use

- Replace placeholder image names with images from ECR, ACR, GCR, or another registry.
- Replace `postgres-secret-example.yaml` with a real secret manager integration.
- Put FastAPI behind an ingress controller with HTTPS.
- Use managed PostgreSQL instead of an in-cluster database.
- Use managed Kafka and cloud object storage for the data lake.
- Add resource requests/limits and horizontal pod autoscaling.

## Validate Manifests

```bash
kubectl apply --dry-run=client -f infra/k8s
```
