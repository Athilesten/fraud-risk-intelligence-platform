# Security And Compliance Review

This checklist is professional guidance, not legal advice.

## Threat Model

- Unauthorized API access
- Stolen API keys or JWTs
- Data leakage from logs
- Poisoned Kafka events
- Model abuse through high-volume requests
- Database exposure
- Insecure cloud storage access

## Authentication

- Local API key and demo JWT are acceptable for demos.
- Production should use OAuth2/OIDC through Auth0, Okta, Entra ID, or Keycloak.
- Tokens must validate issuer, audience, expiry, and signature.

## Authorization

- Use RBAC roles: admin, risk analyst, data engineer, viewer.
- Backend enforcement is mandatory.
- Frontend hiding is convenience, not security.

## API Security

- HTTPS only in production
- Rate limits
- Request size limits
- Structured error responses
- Audit logging for sensitive actions

## Data Privacy

- Avoid storing raw PII where not required.
- Hash/tokenize account identifiers.
- Encrypt data at rest and in transit.
- Restrict Bronze data access.

## Compliance Awareness

| Area | Control Theme |
|---|---|
| GDPR-style privacy | Data minimization, retention, access control |
| PCI-DSS awareness | Payment data protection and network segmentation |
| SOC2-style controls | Change management, monitoring, access review |
| RBI/financial audit awareness | Audit trails, incident response, data governance |

## Incident Response

- Alert on API failures and fraud spikes.
- Keep runbooks for Kafka, API, database, and model incidents.
- Preserve audit logs for investigation.
