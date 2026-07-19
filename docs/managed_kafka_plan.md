# Managed Kafka Plan

## Local vs Managed Kafka

| Area | Local Docker Kafka | Managed Kafka |
|---|---|---|
| Purpose | Demo and development | Production ingestion |
| Operations | Manual Docker lifecycle | Provider-managed brokers |
| Security | Plaintext local broker | TLS, IAM/SASL, private networking |
| Scaling | Single broker | Multi-broker, multi-AZ |
| Monitoring | Kafka UI and logs | Broker metrics, lag metrics, alerts |

## Production Options

- AWS: Amazon MSK
- Azure: Confluent Cloud or Event Hubs Kafka API
- GCP: Confluent Cloud

## Topic Strategy

| Topic | Purpose |
|---|---|
| `fraud.transactions.raw` | Raw transaction events |
| `fraud.transactions.scored` | Scored fraud decisions |
| `fraud.transactions.errors` | Invalid messages and failed scoring events |

## Partitioning

Use `sender_id`, account id, or transaction id as the message key. Start with 3-6 partitions for demo-scale production, then tune using throughput and consumer lag.

## Retention

- Raw events: 7-30 days
- Scored events: 30-90 days
- Error topic: 30 days or until triaged

## Consumer Groups

- `fraud-scoring-consumer-group`
- `spark-raw-datalake-consumer`
- `spark-scored-datalake-consumer`

## Security

- TLS for all broker connections
- SASL/SCRAM, IAM auth, or managed identity
- Private subnets/private endpoints
- Credentials stored in secret manager

## Monitoring

Track broker health, topic throughput, consumer lag, failed messages, and dead-letter volume.
