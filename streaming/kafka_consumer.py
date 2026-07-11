import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import requests
from kafka import KafkaConsumer


KAFKA_TOPIC = "transactions"
KAFKA_BOOTSTRAP_SERVER = "localhost:9092"

FASTAPI_URL = "http://127.0.0.1:8000/predict"

BASE_DIR = Path(__file__).resolve().parent.parent
KAFKA_LOG_PATH = BASE_DIR / "data" / "processed" / "kafka_scored_transactions.csv"


def save_kafka_log(transaction, prediction):
    KAFKA_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    log_row = {
        "scored_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transaction_id": transaction.get("transaction_id"),
        "event_time": transaction.get("event_time"),
        "step": transaction.get("step"),
        "type": transaction.get("type"),
        "amount": transaction.get("amount"),
        "oldbalanceOrg": transaction.get("oldbalanceOrg"),
        "newbalanceOrig": transaction.get("newbalanceOrig"),
        "oldbalanceDest": transaction.get("oldbalanceDest"),
        "newbalanceDest": transaction.get("newbalanceDest"),
        "isFlaggedFraud": transaction.get("isFlaggedFraud"),
        "fraud_probability": prediction.get("fraud_probability"),
        "ml_risk_level": prediction.get("risk_level"),
        "alert": prediction.get("alert"),
        "rule_risk_score": prediction.get("rule_risk_score"),
        "rule_risk_level": prediction.get("rule_risk_level"),
        "triggered_rules": " | ".join(prediction.get("triggered_rules", [])),
        "final_decision": prediction.get("final_decision")
    }

    new_df = pd.DataFrame([log_row])

    if KAFKA_LOG_PATH.exists():
        old_df = pd.read_csv(KAFKA_LOG_PATH)
        final_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        final_df = new_df

    final_df.to_csv(KAFKA_LOG_PATH, index=False)


def create_consumer():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVER,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="fraud-risk-consumer-group",
        value_deserializer=lambda value: json.loads(value.decode("utf-8"))
    )

    return consumer


def clean_transaction_for_api(transaction):
    return {
        "step": int(transaction["step"]),
        "type": str(transaction["type"]).upper(),
        "amount": float(transaction["amount"]),
        "oldbalanceOrg": float(transaction["oldbalanceOrg"]),
        "newbalanceOrig": float(transaction["newbalanceOrig"]),
        "oldbalanceDest": float(transaction["oldbalanceDest"]),
        "newbalanceDest": float(transaction["newbalanceDest"]),
        "isFlaggedFraud": int(transaction["isFlaggedFraud"])
    }


def run_consumer():
    consumer = create_consumer()

    print("Kafka Consumer Started")
    print(f"Listening to topic: {KAFKA_TOPIC}")
    print("Press CTRL + C to stop")
    print("-" * 60)

    try:
        for message in consumer:
            transaction = message.value

            api_transaction = clean_transaction_for_api(transaction)

            try:
                response = requests.post(
                    FASTAPI_URL,
                    json=api_transaction,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    prediction = result["prediction"]

                    save_kafka_log(transaction, prediction)

                    print(
                        f"Scored {transaction.get('transaction_id')} | "
                        f"{transaction.get('type')} | "
                        f"Amount: {transaction.get('amount')} | "
                        f"ML Risk: {prediction.get('risk_level')} | "
                        f"Rule Score: {prediction.get('rule_risk_score')} | "
                        f"Decision: {prediction.get('final_decision')}"
                    )

                else:
                    print("FastAPI Error:")
                    print(response.json())

            except requests.exceptions.ConnectionError:
                print("FastAPI server is not running.")
                print("Run this first: uvicorn api.main:app --reload")
                break

            except Exception as e:
                print(f"Error while scoring transaction: {e}")

    except KeyboardInterrupt:
        print("Kafka Consumer stopped by user.")

    finally:
        consumer.close()


if __name__ == "__main__":
    run_consumer()