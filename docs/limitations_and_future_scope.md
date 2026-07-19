# Limitations And Future Scope

## Honest Current Limitations

- This is a production-style local implementation, not a deployed bank production system.
- JWT login is a local demo flow, not a full enterprise identity provider.
- API key support remains for local service-to-service calls.
- Delta Lake runs locally, not on S3, ADLS, or GCS.
- Kafka schemas are lightweight JSON validation, not a full Schema Registry deployment.
- Spark pipelines are designed for local demo scale.
- Grafana dashboards are provisioned, but production alerting rules are not fully built out.

## Future Enterprise Improvements

- Kubernetes deployment
- HTTPS and ingress controller
- Secret manager integration
- OAuth/OIDC provider
- Full role-based access control
- Managed Kafka or Redpanda
- Cloud data lake on S3, ADLS, or GCS
- Schema Registry with Avro/Protobuf compatibility checks
- Load testing and capacity planning
- Centralized logging stack
- Security/compliance review
- Blue/green or canary deployment pipeline
