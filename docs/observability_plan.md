# Observability Plan

## Metrics

Prometheus collects:

- API request count
- Error count/rate
- Latency histogram
- P95 latency
- Prediction count
- Risk levels
- Final decisions

## Logs

FastAPI emits structured JSON logs with request id, path, status code, duration, and error details.

## Alerts

Prometheus alert rules cover:

- API server errors
- High p95 latency
- High-risk fraud prediction spike

## Dashboards

Grafana dashboard should show:

- Total requests
- Request rate
- Error count
- Average/P95 latency
- Fraud predictions by risk level
- Final decisions

## Future Tracing

Add OpenTelemetry tracing from React -> FastAPI -> PostgreSQL/Kafka for distributed debugging in production.
