# Managed PostgreSQL Plan

## Local vs Managed PostgreSQL

Local PostgreSQL is for demos. Production should use a managed database with backups, encryption, private networking, and monitoring.

## Cloud Mapping

| Cloud | Service |
|---|---|
| AWS | Amazon RDS PostgreSQL |
| Azure | Azure Database for PostgreSQL |
| GCP | Cloud SQL for PostgreSQL |

## Production Requirements

- Private networking only
- Encryption at rest
- TLS connections
- Automated backups
- Point-in-time recovery
- Database monitoring and alerting
- Least-privilege application user
- Alembic migrations for schema changes

## Connection Pooling

Use PgBouncer or managed pooling when traffic grows. FastAPI should use a bounded pool to avoid exhausting database connections.

## Migration Strategy

Use Alembic:

```cmd
set DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/fraud_db
.\venv\Scripts\alembic.exe upgrade head
```

The local API fallback table creation remains for demos only.

## Disaster Recovery

- Daily backups
- PITR enabled
- Restore drill tested quarterly
- Read replica for reporting or failover where available
