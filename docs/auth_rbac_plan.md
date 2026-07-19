# Authentication And RBAC Plan

## Current Local Auth

- `X-API-Key` supports local service-to-service calls.
- Demo JWT login supports local product-demo access.
- API key keeps full `service` permissions for scripts, Streamlit, and React local demo.

## Roles

| Role | Intended Access |
|---|---|
| `admin` | Full access |
| `risk_analyst` | Prediction, batch scoring, logs, monitoring |
| `data_engineer` | Streaming, data lake, monitoring |
| `viewer` | Read-only logs and monitoring |
| `service` | Internal service/API-key access |

## Current Permissions

Permissions are defined in `src/rbac.py` and enforced in FastAPI through endpoint dependencies.

## Enterprise SSO Options

- Auth0
- Okta
- Microsoft Entra ID
- Keycloak for self-hosted/local enterprise identity

## Production Plan

Replace demo JWT with OAuth2/OIDC:

```text
Browser -> Identity Provider -> Access Token -> FastAPI JWT validation -> RBAC
```

FastAPI should validate issuer, audience, signature, expiry, and role/group claims.

## React Behavior

React should hide restricted controls when `/auth/me` returns a lower-privilege role. Backend authorization remains the source of truth.
