# CI/CD Plan

## Current CI

GitHub Actions validates:

- Python dependencies
- Backend and streaming compile checks
- Pytest suite
- Docker Compose config
- Frontend install and build

## Docker Build Workflow

The optional `docker-build.yml` workflow builds API and frontend images. It does not push images because no registry credentials are required.

## Future Pipeline

```text
Pull Request -> Tests -> Docker Build -> Security Scan -> Staging Deploy -> Approval -> Production Deploy
```

## Promotion

- `dev`: every merge to main
- `staging`: release candidate
- `prod`: approved version only

## Rollback

- Keep previous container images.
- Keep previous model version.
- Roll back database migrations only with reviewed downgrade scripts.
