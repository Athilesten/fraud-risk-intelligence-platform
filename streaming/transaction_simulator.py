from pathlib import Path
from datetime import datetime
import random
import time

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parent.parent
REALTIME_LOG_PATH = BASE_DIR / "data" / "processed" / "realtime_simulation_log.csv"

API_URL = "http://127.0.0.1:8000/predict"


def generate_transaction(transaction_id):
    txn_types = ["PAYMENT", "TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT"]

    txn_type = random.choices(
        txn_types,
        weights=[45, 20, 25, 7, 3],
        k=1
    )[0]

    # Around 10% suspicious transactions for demo
    suspicious = random.random() < 0.10

    if suspicious and txn_type in ["TRANSFER", "CASH_OUT"]:
        amount = round(random.uniform(200000, 600000), 2)
        oldbalance_org = amount
        newbalance_orig = 0.0
        oldbalance_dest = round(random.uniform(0, 50000), 2)
        newbalance_dest = oldbalance_dest + amount
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
            newbalance_orig = oldbalance_org + amount
        else:
            newbalance_orig = max(oldbalance_org - amount, 0)

        oldbalance_dest = round(random.uniform(0, 200000), 2)

        if txn_type in ["TRANSFER", "CASH_OUT"]:
            newbalance_dest = oldbalance_dest + amount
        else:
            newbalance_dest = oldbalance_dest

        is_flagged_fraud = 0

    transaction = {
        "step": random.randint(1, 744),
        "type": txn_type,
        "amount": float(round(amount, 2)),
        "oldbalanceOrg": float(round(oldbalance_org, 2)),
        "newbalanceOrig": float(round(newbalance_orig, 2)),
        "oldbalanceDest": float(round(oldbalance_dest, 2)),
        "newbalanceDest": float(round(newbalance_dest, 2)),
        "isFlaggedFraud": int(is_flagged_fraud)
    }

    return transaction


def save_realtime_log(transaction_id, transaction, prediction):
    REALTIME_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    log_row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transaction_id": transaction_id,
        "step": transaction["step"],
        "type": transaction["type"],
        "amount": transaction["amount"],
        "oldbalanceOrg": transaction["oldbalanceOrg"],
        "newbalanceOrig": transaction["newbalanceOrig"],
        "oldbalanceDest": transaction["oldbalanceDest"],
        "newbalanceDest": transaction["newbalanceDest"],
        "isFlaggedFraud": transaction["isFlaggedFraud"],
        "fraud_probability": prediction["fraud_probability"],
        "ml_risk_level": prediction["risk_level"],
        "rule_risk_score": prediction.get("rule_risk_score", 0),
        "rule_risk_level": prediction.get("rule_risk_level", "LOW"),
        "triggered_rules": " | ".join(prediction.get("triggered_rules", [])),
        "final_decision": prediction.get("final_decision", "APPROVE"),
        "alert": prediction.get("alert", "")
    }

    new_df = pd.DataFrame([log_row])

    if REALTIME_LOG_PATH.exists():
        old_df = pd.read_csv(REALTIME_LOG_PATH)
        final_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        final_df = new_df

    final_df.to_csv(REALTIME_LOG_PATH, index=False)


def run_simulator(total_transactions=20, delay_seconds=2):
    print("Real-Time Transaction Simulator Started")
    print("Sending transactions to:", API_URL)
    print("-" * 60)

    for transaction_id in range(1, total_transactions + 1):
        transaction = generate_transaction(transaction_id)

        try:
            response = requests.post(API_URL, json=transaction, timeout=30)

            if response.status_code == 200:
                result = response.json()
                prediction = result["prediction"]

                save_realtime_log(transaction_id, transaction, prediction)

                print(
                    f"TXN-{transaction_id} | "
                    f"{transaction['type']} | "
                    f"Amount: {transaction['amount']} | "
                    f"ML Risk: {prediction['risk_level']} | "
                    f"Rule Score: {prediction.get('rule_risk_score', 0)} | "
                    f"Decision: {prediction.get('final_decision', 'APPROVE')}"
                )

            else:
                print(f"TXN-{transaction_id} failed")
                print(response.json())

        except requests.exceptions.ConnectionError:
            print("FastAPI server is not running.")
            print("Run this first: uvicorn api.main:app --reload")
            break

        except Exception as e:
            print(f"Error in TXN-{transaction_id}: {e}")

        time.sleep(delay_seconds)

    print("-" * 60)
    print("Simulation completed.")
    print("Saved log at:", REALTIME_LOG_PATH)


if __name__ == "__main__":
    run_simulator(total_transactions=20, delay_seconds=2)