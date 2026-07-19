# Secrets Management Plan

## Local Demo

Local development uses `.env`. This is acceptable only for demos.

Sensitive values:

- `FRAUD_API_KEY`
- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `POSTGRES_PASSWORD`
- `GRAFANA_ADMIN_PASSWORD`
- `KAFKA_USERNAME`
- `KAFKA_PASSWORD`
- OIDC client settings

## Production Options

| Environment | Secret Store |
|---|---|
| AWS | AWS Secrets Manager |
| Azure | Azure Key Vault |
| GCP | Secret Manager |
| Docker Swarm | Docker secrets |
| GitHub Actions | GitHub Actions Secrets |

## Rotation

- Rotate API keys and JWT signing secrets regularly.
- Rotate database passwords using managed database tooling.
- Rotate Kafka credentials through managed Kafka provider.
- Keep old and new secrets active during short migration windows.

## Rules

- Never commit real secrets.
- Do not put secrets in Docker images.
- Do not print secrets in logs.
- Prefer managed identity where possible.
