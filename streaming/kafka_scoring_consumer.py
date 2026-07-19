import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from kafka import KafkaConsumer, KafkaProducer

from schema_validator import (
    SchemaValidationError,
    validate_raw_event,
    validate_scored_event,
)


BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
SCORED_LOG_PATH = PROCESSED_DIR / "kafka_scored_transactions.csv"
DEAD_LETTER_PATH = PROCESSED_DIR / "kafka_dead_letter_transactions.csv"

KAFKA_BOOTSTRAP_SERVERS = os.environ.get(
    "KAFKA_BOOTSTRAP_SERVERS",
    os.environ.get("KAFKA_BOOTSTRAP_SERVER", "localhost:9092")
)
KAFKA_RAW_TOPIC = os.environ.get(
    "KAFKA_RAW_TOPIC",
    os.environ.get("KAFKA_TOPIC", "transactions.raw")
)
KAFKA_SCORED_TOPIC = os.environ.get("KAFKA_SCORED_TOPIC", "transactions.scored")
KAFKA_ERRORS_TOPIC = os.environ.get(
    "KAFKA_ERRORS_TOPIC",
    os.environ.get("KAFKA_ERROR_TOPIC", "transactions.errors")
)

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
FRAUD_API_URL = os.environ.get("FRAUD_API_URL", f"{API_BASE_URL}/predict")
FRAUD_API_KEY = os.environ.get("FRAUD_API_KEY", "dev_fraud_api_key_123")
MAX_API_RETRIES = int(os.environ.get("MAX_API_RETRIES", "3"))


REQUIRED_API_FIELDS = [
    "step",
    "type",
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
    "isFlaggedFraud",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def create_consumer():
    return KafkaConsumer(
        KAFKA_RAW_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="fraud-scoring-consumer-group",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )


def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        key_serializer=lambda value: str(value).encode("utf-8"),
        value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
        retries=3,
    )


def transaction_for_api(event):
    missing = [field for field in REQUIRED_API_FIELDS if field not in event]
    if missing:
        raise ValueError(f"Missing required transaction fields: {', '.join(missing)}")

    return {
        "step": int(event["step"]),
        "type": str(event["type"]).upper(),
        "amount": float(event["amount"]),
        "oldbalanceOrg": float(event["oldbalanceOrg"]),
        "newbalanceOrig": float(event["newbalanceOrig"]),
        "oldbalanceDest": float(event["oldbalanceDest"]),
        "newbalanceDest": float(event["newbalanceDest"]),
        "isFlaggedFraud": int(event["isFlaggedFraud"]),
    }


def post_prediction(api_transaction):
    if not FRAUD_API_KEY:
        raise RuntimeError("FRAUD_API_KEY is required for streaming scoring.")

    last_error = None

    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            response = requests.post(
                FRAUD_API_URL,
                json=api_transaction,
                headers={"X-API-Key": FRAUD_API_KEY},
                timeout=30,
            )
            if response.status_code == 200:
                return response.json()
            last_error = f"FastAPI returned {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as exc:
            last_error = str(exc)

        time.sleep(min(2 ** attempt, 10))

    raise RuntimeError(last_error or "FastAPI scoring request failed.")


def append_csv(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    new_df = pd.DataFrame([row])

    if path.exists():
        old_df = pd.read_csv(path)
        new_df = pd.concat([old_df, new_df], ignore_index=True)

    new_df.to_csv(path, index=False)


def save_scored_log(scored_event):
    prediction = scored_event["prediction"]

    append_csv(
        SCORED_LOG_PATH,
        {
            "scored_at": scored_event["scored_at"],
            "event_id": scored_event.get("event_id"),
            "event_time": scored_event.get("event_time"),
            "source_dataset": scored_event.get("source_dataset"),
            "type": scored_event.get("type"),
            "amount": scored_event.get("amount"),
            "fraud_probability": prediction.get("fraud_probability"),
            "risk_level": prediction.get("risk_level"),
            "rule_risk_score": prediction.get("rule_risk_score"),
            "rule_risk_level": prediction.get("rule_risk_level"),
            "final_decision": prediction.get("final_decision"),
            "triggered_rules": " | ".join(prediction.get("triggered_rules", [])),
        },
    )


def save_dead_letter(event, error_message):
    append_csv(
        DEAD_LETTER_PATH,
        {
            "failed_at": now_iso(),
            "event_id": event.get("event_id"),
            "source_dataset": event.get("source_dataset"),
            "error_message": error_message,
            "raw_event": json.dumps(event, default=str),
        },
    )


def publish_error(producer, event, error_message):
    error_event = {
        "failed_at": now_iso(),
        "event": event,
        "error_message": error_message,
    }
    producer.send(
        KAFKA_ERRORS_TOPIC,
        key=event.get("event_id", "unknown"),
        value=error_event,
    )
    producer.flush()


def run_consumer(max_records=None):
    try:
        consumer = create_consumer()
        producer = create_producer()
    except Exception as exc:
        print(f"Kafka connection failed: {exc}")
        print(f"Check that Kafka is running at {KAFKA_BOOTSTRAP_SERVERS}.")
        return 1

    print("Kafka scoring consumer started")
    print(f"Raw topic: {KAFKA_RAW_TOPIC}")
    print(f"Scored topic: {KAFKA_SCORED_TOPIC}")
    print(f"FastAPI scoring URL: {FRAUD_API_URL}")
    print("-" * 72)

    processed_count = 0

    try:
        for message in consumer:
            event = message.value

            try:
                validate_raw_event(event)
                api_transaction = transaction_for_api(event)
                api_response = post_prediction(api_transaction)

                scored_event = {
                    **event,
                    "prediction": api_response["prediction"],
                    "explanation": api_response.get("explanation"),
                    "prediction_log_id": api_response.get("prediction_log_id"),
                    "scored_at": now_iso(),
                }
                validate_scored_event(scored_event)

                producer.send(
                    KAFKA_SCORED_TOPIC,
                    key=scored_event.get("event_id", message.offset),
                    value=scored_event,
                )
                producer.flush()
                save_scored_log(scored_event)

                processed_count += 1
                prediction = scored_event["prediction"]
                print(
                    f"scored={processed_count} event_id={scored_event.get('event_id')} "
                    f"risk={prediction.get('risk_level')} "
                    f"decision={prediction.get('final_decision')}"
                )

                if max_records and processed_count >= max_records:
                    break

            except (SchemaValidationError, Exception) as exc:
                error_message = str(exc)
                print(f"bad_event event_id={event.get('event_id')} error={error_message}")
                save_dead_letter(event, error_message)
                try:
                    publish_error(producer, event, error_message)
                except Exception as publish_exc:
                    print(f"Could not publish error event: {publish_exc}")

    except KeyboardInterrupt:
        print("Kafka scoring consumer stopped by user.")

    finally:
        consumer.close()
        producer.close()

    print("-" * 72)
    print(f"Kafka scoring consumer completed. Records scored: {processed_count}")
    return 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Consume transactions.raw, score with FastAPI, publish transactions.scored."
    )
    parser.add_argument("--max-records", type=int, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(run_consumer(max_records=args.max_records))
