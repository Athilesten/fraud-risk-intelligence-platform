import argparse
import csv
import random
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = BASE_DIR / "data" / "raw" / "paysim.csv"
TYPES = ["PAYMENT", "TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT"]


def create_row(index):
    txn_type = random.choices(TYPES, weights=[45, 20, 25, 7, 3], k=1)[0]
    suspicious = txn_type in {"TRANSFER", "CASH_OUT"} and random.random() < 0.15

    if suspicious:
        amount = round(random.uniform(200000, 500000), 2)
        old_org = amount
        new_org = 0.0
        old_dest = round(random.uniform(0, 50000), 2)
        new_dest = old_dest + amount
        is_fraud = 1
        is_flagged = 1
    else:
        amount = round(random.uniform(100, 50000), 2)
        old_org = round(random.uniform(amount, amount + 100000), 2)
        new_org = round(max(old_org - amount, 0), 2)
        old_dest = round(random.uniform(0, 100000), 2)
        new_dest = old_dest + amount if txn_type in {"TRANSFER", "CASH_OUT"} else old_dest
        is_fraud = 0
        is_flagged = 0

    return {
        "step": random.randint(1, 744),
        "type": txn_type,
        "amount": amount,
        "nameOrig": f"C{100000 + index}",
        "oldbalanceOrg": old_org,
        "newbalanceOrig": new_org,
        "nameDest": f"M{200000 + index}",
        "oldbalanceDest": round(old_dest, 2),
        "newbalanceDest": round(new_dest, 2),
        "isFraud": is_fraud,
        "isFlaggedFraud": is_flagged,
    }


def generate_sample(output_path, rows):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "step",
        "type",
        "amount",
        "nameOrig",
        "oldbalanceOrg",
        "newbalanceOrig",
        "nameDest",
        "oldbalanceDest",
        "newbalanceDest",
        "isFraud",
        "isFlaggedFraud",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for index in range(1, rows + 1):
            writer.writerow(create_row(index))

    print(f"Sample PaySim-like data written to: {output_path}")
    print(f"Rows: {rows}")


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a small PaySim-like local demo CSV.")
    parser.add_argument("--rows", type=int, default=200)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_sample(Path(args.output), args.rows)
