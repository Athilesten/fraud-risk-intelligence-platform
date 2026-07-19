import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
PAYSIM_PATH = BASE_DIR / "data" / "raw" / "paysim.csv"
IEEE_TRANSACTION_PATH = BASE_DIR / "data" / "raw" / "ieee" / "train_transaction.csv"
IEEE_IDENTITY_PATH = BASE_DIR / "data" / "raw" / "ieee" / "train_identity.csv"


CANONICAL_COLUMNS = [
    "event_id",
    "event_time",
    "source_dataset",
    "step",
    "type",
    "amount",
    "sender_id",
    "receiver_id",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
    "isFlaggedFraud",
    "isFraud",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def safe_float(value, default=0.0):
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    if pd.isna(value):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_paysim(df):
    records = []

    for _, row in df.iterrows():
        records.append({
            "event_id": str(row.get("event_id") or row.get("transaction_id") or uuid.uuid4()),
            "event_time": str(row.get("event_time") or now_iso()),
            "source_dataset": "paysim",
            "step": safe_int(row.get("step")),
            "type": str(row.get("type", "TRANSFER")).upper(),
            "amount": safe_float(row.get("amount")),
            "sender_id": str(row.get("nameOrig") or row.get("sender_id") or ""),
            "receiver_id": str(row.get("nameDest") or row.get("receiver_id") or ""),
            "oldbalanceOrg": safe_float(row.get("oldbalanceOrg")),
            "newbalanceOrig": safe_float(row.get("newbalanceOrig")),
            "oldbalanceDest": safe_float(row.get("oldbalanceDest")),
            "newbalanceDest": safe_float(row.get("newbalanceDest")),
            "isFlaggedFraud": safe_int(row.get("isFlaggedFraud")),
            "isFraud": safe_int(row.get("isFraud")),
        })

    return records


def normalize_ieee(df):
    records = []

    for _, row in df.iterrows():
        transaction_id = str(row.get("TransactionID") or uuid.uuid4())
        amount = safe_float(row.get("TransactionAmt"))
        transaction_dt = safe_int(row.get("TransactionDT"))

        records.append({
            "event_id": transaction_id,
            "event_time": now_iso(),
            "source_dataset": "ieee-cis",
            "step": transaction_dt,
            "type": str(row.get("ProductCD") or "IEEE").upper(),
            "amount": amount,
            "sender_id": str(row.get("card1") or row.get("addr1") or ""),
            "receiver_id": str(row.get("addr2") or row.get("P_emaildomain") or ""),
            "oldbalanceOrg": 0.0,
            "newbalanceOrig": 0.0,
            "oldbalanceDest": 0.0,
            "newbalanceDest": 0.0,
            "isFlaggedFraud": 0,
            "isFraud": safe_int(row.get("isFraud")),
        })

    return records


def load_transactions(dataset="paysim", max_records=None):
    dataset = dataset.lower().strip()

    if dataset == "paysim":
        if not PAYSIM_PATH.exists():
            raise FileNotFoundError(f"PaySim file not found: {PAYSIM_PATH}")

        df = pd.read_csv(PAYSIM_PATH)
        if max_records:
            df = df.head(max_records)
        return normalize_paysim(df)

    if dataset == "ieee":
        if not IEEE_TRANSACTION_PATH.exists():
            raise FileNotFoundError(f"IEEE transaction file not found: {IEEE_TRANSACTION_PATH}")

        df = pd.read_csv(IEEE_TRANSACTION_PATH)

        if IEEE_IDENTITY_PATH.exists():
            identity_df = pd.read_csv(IEEE_IDENTITY_PATH)
            df = df.merge(identity_df, on="TransactionID", how="left")

        if max_records:
            df = df.head(max_records)
        return normalize_ieee(df)

    raise ValueError("dataset must be either 'paysim' or 'ieee'")
