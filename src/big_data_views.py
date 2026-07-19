import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
DATA_LAKE_PATH = Path(os.environ.get("DATA_LAKE_PATH", DATA_DIR / "delta"))

KAFKA_SCORED_LOG_PATH = PROCESSED_DIR / "kafka_scored_transactions.csv"
KAFKA_DEAD_LETTER_PATH = PROCESSED_DIR / "kafka_dead_letter_transactions.csv"

DELTA_TABLE_CANDIDATES = {
    "bronze": [
        DATA_LAKE_PATH / "bronze" / "transactions_raw",
        DATA_LAKE_PATH / "raw_transactions",
    ],
    "silver": [
        DATA_LAKE_PATH / "silver" / "transactions_features",
        DATA_LAKE_PATH / "curated_transactions",
    ],
    "gold": [
        DATA_LAKE_PATH / "gold" / "fraud_risk_summary",
    ],
    "scored_gold": [
        DATA_LAKE_PATH / "gold" / "scored_fraud_decisions",
    ],
}


def file_status(path):
    return {
        "path": str(path),
        "exists": path.exists(),
        "updated_at": (
            datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            if path.exists()
            else None
        ),
    }


def read_recent_csv(path, limit=20):
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    return rows[-limit:][::-1]


def delta_log_files(table_path):
    log_dir = table_path / "_delta_log"
    if not log_dir.exists():
        return []
    return sorted(log_dir.glob("*.json"))


def delta_table_count(table_path):
    total_records = 0
    latest_timestamp = None

    for log_file in delta_log_files(table_path):
        latest_timestamp = datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()

        with log_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    action = json.loads(line)
                except json.JSONDecodeError:
                    continue

                add_action = action.get("add")
                if not add_action:
                    continue

                stats = add_action.get("stats")
                if not stats:
                    continue

                try:
                    stats_data = json.loads(stats)
                except json.JSONDecodeError:
                    continue

                total_records += int(stats_data.get("numRecords", 0))

    return {
        "exists": table_path.exists(),
        "path": str(table_path),
        "count": total_records,
        "latest_ingestion_timestamp": latest_timestamp,
    }


def resolve_delta_table(table_name):
    candidates = DELTA_TABLE_CANDIDATES[table_name]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def get_streaming_status():
    scored_status = file_status(KAFKA_SCORED_LOG_PATH)
    dead_letter_status = file_status(KAFKA_DEAD_LETTER_PATH)
    delta_statuses = {
        name: delta_table_count(resolve_delta_table(name))
        for name in DELTA_TABLE_CANDIDATES
    }

    return {
        "kafka": {
            "bootstrap_servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            "raw_topic": os.environ.get("KAFKA_RAW_TOPIC", "transactions.raw"),
            "scored_topic": os.environ.get("KAFKA_SCORED_TOPIC", "transactions.scored"),
            "errors_topic": os.environ.get(
                "KAFKA_ERRORS_TOPIC",
                os.environ.get("KAFKA_ERROR_TOPIC", "transactions.errors")
            ),
            "recent_scored_log": scored_status,
            "dead_letter_log": dead_letter_status,
        },
        "fastapi_scoring": {
            "status": "available",
            "endpoint": "/predict",
        },
        "data_lake": {
            "base_path": str(DATA_LAKE_PATH),
            "available": any(status["exists"] for status in delta_statuses.values()),
            "tables": delta_statuses,
        },
        "last_refresh_time": datetime.now(timezone.utc).isoformat(),
    }


def get_recent_scored(limit=20):
    rows = read_recent_csv(KAFKA_SCORED_LOG_PATH, limit=limit)

    return {
        "total_records": len(rows),
        "records": rows,
        "source": str(KAFKA_SCORED_LOG_PATH),
        "available": KAFKA_SCORED_LOG_PATH.exists(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_datalake_summary():
    table_counts = {
        name: delta_table_count(resolve_delta_table(name))
        for name in DELTA_TABLE_CANDIDATES
    }

    latest_ingestion_timestamp = None
    for status in table_counts.values():
        timestamp = status.get("latest_ingestion_timestamp")
        if timestamp and (latest_ingestion_timestamp is None or timestamp > latest_ingestion_timestamp):
            latest_ingestion_timestamp = timestamp

    recent_scored = read_recent_csv(KAFKA_SCORED_LOG_PATH, limit=200)
    type_distribution = {}
    latest_event_timestamp = None

    for row in recent_scored:
        txn_type = row.get("type") or "UNKNOWN"
        type_distribution[txn_type] = type_distribution.get(txn_type, 0) + 1
        event_timestamp = row.get("event_time")
        if event_timestamp and (latest_event_timestamp is None or event_timestamp > latest_event_timestamp):
            latest_event_timestamp = event_timestamp

    return {
        "bronze_count": table_counts["bronze"]["count"],
        "silver_count": table_counts["silver"]["count"],
        "gold_count": table_counts["gold"]["count"],
        "scored_gold_count": table_counts["scored_gold"]["count"],
        "latest_event_timestamp": latest_event_timestamp,
        "latest_ingestion_timestamp": latest_ingestion_timestamp,
        "transaction_type_distribution": [
            {"type": txn_type, "count": count}
            for txn_type, count in sorted(type_distribution.items())
        ],
        "tables": table_counts,
        "available": any(status["exists"] for status in table_counts.values()),
        "empty_state_command": "python streaming\\spark_streaming_delta_pipeline.py",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
