import json
import random
import time
from datetime import datetime

from kafka import KafkaProducer


KAFKA_TOPIC = "transactions"
KAFKA_BOOTSTRAP_SERVER = "localhost:9092"


def generate_transaction(transaction_id):
    txn_types = ["PAYMENT", "TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT"]

    txn_type = random.choices(
        txn_types,
        weights=[45, 20, 25, 7, 3],
        k=1
    )[0]

    suspicious = random.random() < 0.10

    if suspicious and txn_type in ["TRANSFER", "CASH_OUT"]:
        amount = round(random.uniform(200000, 600000), 2)
        oldbalance_org = amount
        newbalance_orig = 0.0
        oldbalance_dest = round(random.uniform(0, 50000), 2)
        newbalance_dest = round(oldbalance_dest + amount, 2)
        is_flagged_fraud = 1 if amount >= 200000 else 0

    else:
        if txn_type == "PAYMENT":
            amount = round(random.uniform(100, 20000), 2)
        elif txn_type in ["TRANSFER", "CASH_OUT"]:
            amount = round(random.uniform(1000, 100000), 2)
        elif txn_type == "CASH_IN":
            amount = round(random.uniform(500, 80000), 2)
        else:
            amount = round(random.uniform(100, 10000), 2)

        oldbalance_org = round(random.uniform(amount, amount + 200000), 2)

        if txn_type == "CASH_IN":
            newbalance_orig = round(oldbalance_org + amount, 2)
        else:
            newbalance_orig = round(max(oldbalance_org - amount, 0), 2)

        oldbalance_dest = round(random.uniform(0, 200000), 2)

        if txn_type in ["TRANSFER", "CASH_OUT"]:
            newbalance_dest = round(oldbalance_dest + amount, 2)
        else:
            newbalance_dest = oldbalance_dest

        is_flagged_fraud = 0

    transaction = {
        "transaction_id": f"TXN-{transaction_id}",
        "event_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "step": random.randint(1, 744),
        "type": txn_type,
        "amount": float(amount),
        "oldbalanceOrg": float(oldbalance_org),
        "newbalanceOrig": float(newbalance_orig),
        "oldbalanceDest": float(oldbalance_dest),
        "newbalanceDest": float(newbalance_dest),
        "isFlaggedFraud": int(is_flagged_fraud)
    }

    return transaction


def create_producer():
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVER,
        value_serializer=lambda value: json.dumps(value).encode("utf-8")
    )

    return producer


def run_producer(total_transactions=50, delay_seconds=1):
    producer = create_producer()

    print("Kafka Producer Started")
    print(f"Sending data to topic: {KAFKA_TOPIC}")
    print("-" * 60)

    for transaction_id in range(1, total_transactions + 1):
        transaction = generate_transaction(transaction_id)

        producer.send(KAFKA_TOPIC, value=transaction)
        producer.flush()

        print(
            f"Sent {transaction['transaction_id']} | "
            f"{transaction['type']} | "
            f"Amount: {transaction['amount']}"
        )

        time.sleep(delay_seconds)

    producer.close()

    print("-" * 60)
    print("Kafka Producer Completed")


if __name__ == "__main__":
    run_producer(total_transactions=50, delay_seconds=1)