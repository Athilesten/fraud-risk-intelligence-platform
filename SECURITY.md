# Security Notes

## Secrets

Create a local `.env` from `.env.example` and set strong values for:

- `FRAUD_API_KEY`
- `POSTGRES_PASSWORD`
- `GRAFANA_ADMIN_PASSWORD`

Do not commit `.env`, private datasets, model files, logs, or local databases.

## API Authentication

Protected endpoints require the `X-API-Key` header:

- `POST /predict`
- `POST /predict_batch`
- `GET /prediction_logs`
- `GET /monitoring/metrics`

The backend does not ship with a default API key. If `FRAUD_API_KEY` is missing, protected routes fail closed.

## Frontend Key Handling

The React frontend lets the local analyst enter an API key for demo usage. In a real deployment, use a backend session, OAuth/OIDC, or a gateway token exchange instead of exposing long-lived service keys in the browser.

## CORS

Allowed browser origins are configured with `FRAUD_CORS_ORIGINS`.

Example:

```env
FRAUD_CORS_ORIGINS=http://localhost:5173,https://risk-console.example.com
```

## Logging

The API writes structured JSON request logs and stores prediction audit records in PostgreSQL. Production systems should additionally:

- mask sensitive customer identifiers
- use centralized log retention
- restrict dashboard access by role
- track manual review decisions
- alert on authentication failures and API error spikes

## Production Hardening Backlog

- replace API-key auth with identity-aware access
- add rate limiting
- add request size limits
- add TLS termination at a reverse proxy or gateway
- run dependency and container image scans in CI
- add database migrations instead of table creation at app startup
