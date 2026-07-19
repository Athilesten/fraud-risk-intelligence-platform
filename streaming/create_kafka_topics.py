import os

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import KafkaError, NoBrokersAvailable, TopicAlreadyExistsError


KAFKA_BOOTSTRAP_SERVERS = os.environ.get(
    "KAFKA_BOOTSTRAP_SERVERS",
    os.environ.get("KAFKA_BOOTSTRAP_SERVER", "localhost:9092")
)
TOPICS = [
    os.environ.get("KAFKA_RAW_TOPIC", "transactions.raw"),
    os.environ.get("KAFKA_SCORED_TOPIC", "transactions.scored"),
    os.environ.get("KAFKA_ERRORS_TOPIC", os.environ.get("KAFKA_ERROR_TOPIC", "transactions.errors")),
]


def create_topics():
    try:
        admin = KafkaAdminClient(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            client_id="fraud-risk-topic-admin",
            request_timeout_ms=15000,
        )
    except NoBrokersAvailable:
        print("Kafka broker is not available.")
        print(f"Expected bootstrap server: {KAFKA_BOOTSTRAP_SERVERS}")
        print("Start Kafka first: scripts\\start_streaming_stack.bat")
        print("Then wait 45-60 seconds and run this command again.")
        return 1
    except KafkaError as exc:
        print(f"Kafka admin connection failed: {exc}")
        print("Check Docker Desktop and the streaming stack logs: docker logs fraud_kafka --tail 80")
        return 1

    existing_topics = set(admin.list_topics())
    new_topics = [
        NewTopic(name=topic, num_partitions=1, replication_factor=1)
        for topic in TOPICS
        if topic not in existing_topics
    ]

    if not new_topics:
        print("Kafka topics already exist:")
        for topic in TOPICS:
            print(f"- {topic}")
        admin.close()
        return

    try:
        admin.create_topics(new_topics=new_topics, validate_only=False)
        print("Kafka topics created:")
        for topic in new_topics:
            print(f"- {topic.name}")
    except TopicAlreadyExistsError:
        print("Some topics already existed; continuing.")
    finally:
        admin.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(create_topics())
