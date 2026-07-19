# Cloud Data Lake Plan

## Local vs Cloud Lake

Local Delta Lake writes to `data/delta`. Production should write to object storage such as S3, ADLS Gen2, or GCS.

## Bronze/Silver/Gold Layout

```text
fraud-risk-datalake/
  bronze/transactions_raw/
  silver/transactions_features/
  gold/fraud_risk_summary/
  gold/scored_fraud_decisions/
```

## Partitioning

Recommended partitions:

- `event_date`
- `source_dataset`
- Optional: `transaction_type`

Avoid over-partitioning small tables.

## Retention

- Bronze: immutable raw retention based on compliance policy
- Silver: feature-enriched analytical data
- Gold: aggregated reporting and model monitoring outputs

## PII Handling

- Tokenize or hash account identifiers.
- Minimize sensitive fields in Gold tables.
- Restrict Bronze access to data engineering and compliance roles.
- Encrypt all data at rest.

## Access Control

- AWS: IAM + Lake Formation
- Azure: RBAC + ACLs on ADLS Gen2
- GCP: IAM + bucket policies

## PySpark Cloud Write Pattern

Use cloud storage paths:

```text
s3a://fraud-risk-datalake/bronze/transactions_raw
abfss://fraud@storage.dfs.core.windows.net/bronze/transactions_raw
gs://fraud-risk-datalake/bronze/transactions_raw
```

Credentials should come from managed identity or secret manager, not source code.
