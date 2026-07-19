# Alerting Strategy

Prometheus scrapes FastAPI metrics from `/metrics`. The local stack also loads `infra/prometheus/alert_rules.yml` so the demo has a production-style alerting story.

## Included Alerts

| Alert | Purpose |
|---|---|
| `FraudApiHighErrorRate` | Detects FastAPI 5xx failures. |
| `FraudApiHighP95Latency` | Detects slow API responses. |
| `FraudHighRiskSpike` | Detects an increase in high-risk fraud predictions. |

## Demo Command

```cmd
cd D:\fraud-risk-intelligence-platform
scripts\start_app_stack.bat
```

Then open:

```text
http://localhost:9090
```

In Prometheus, check **Status -> Rules**.

## Production Extension

For a real deployment, connect Prometheus alerts to Alertmanager, Slack, Teams, PagerDuty, or email. Add Kafka consumer lag alerts when consumer-group lag metrics are available.
