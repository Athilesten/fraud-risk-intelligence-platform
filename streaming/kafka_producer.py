import argparse
import json
import os
import sys
import time
from pathlib import Path

from kafka import KafkaProducer

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from dataset_loader import load_transactions
from schema_validator import SchemaValidationError, validate_raw_event


KAFKA_BOOTSTRAP_SERVERS = os.environ.get(
    "KAFKA_BOOTSTRAP_SERVERS",
    os.environ.get("KAFKA_BOOTSTRAP_SERVER", "localhost:9092")
)
KAFKA_RAW_TOPIC = os.environ.get(
    "KAFKA_RAW_TOPIC",
    os.environ.get("KAFKA_TOPIC", "transactions.raw")
)


def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        key_serializer=lambda value: str(value).encode("utf-8"),
        value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
        retries=3,
    )


def publish_transactions(dataset, max_records, delay_seconds):
    try:
        records = load_transactions(dataset=dataset, max_records=max_records)
    except Exception as exc:
        print(f"Producer stopped: {exc}")
        return 1

    if not records:
        print("Producer stopped: no records available to publish.")
        return 1

    try:
        producer = create_producer()
    except Exception as exc:
        print(f"Kafka connection failed: {exc}")
        print(f"Check that Kafka is running at {KAFKA_BOOTSTRAP_SERVERS}.")
        return 1

    print("Kafka transaction producer started")
    print(f"Dataset: {dataset}")
    print(f"Bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Topic: {KAFKA_RAW_TOPIC}")
    print(f"Records: {len(records)}")
    print("-" * 72)

    sent_count = 0

    try:
        for record in records:
            try:
                validate_raw_event(record)
            except SchemaValidationError as exc:
                print(f"skipped invalid raw event event_id={record.get('event_id')} error={exc}")
                continue

            producer.send(
                KAFKA_RAW_TOPIC,
                key=record["event_id"],
                value=record,
            )
            producer.flush()
            sent_count += 1

            print(
                f"sent={sent_count} event_id={record['event_id']} "
                f"type={record['type']} amount={record['amount']} "
                f"source={record['source_dataset']}"
            )

            if delay_seconds > 0:
                time.sleep(delay_seconds)

    except KeyboardInterrupt:
        print("Producer stopped by user.")

    except Exception as exc:
        print(f"Producer error after {sent_count} records: {exc}")
        return 1

    finally:
        producer.close()

    print("-" * 72)
    print(f"Kafka producer completed. Records sent: {sent_count}")
    return 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Publish canonical fraud transactions to Kafka topic transactions.raw."
    )
    parser.add_argument("--dataset", choices=["paysim", "ieee"], default="paysim")
    parser.add_argument("--max-records", type=int, default=50)
    parser.add_argument("--delay-seconds", type=float, default=0.2)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(
        publish_transactions(
            dataset=args.dataset,
            max_records=args.max_records,
            delay_seconds=args.delay_seconds,
        )
    )
