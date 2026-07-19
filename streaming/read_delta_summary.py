import argparse
import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from big_data_views import get_datalake_summary, get_recent_scored, get_streaming_status


def parse_args():
    parser = argparse.ArgumentParser(description="Show local Kafka and Delta Lake demo status.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def print_human_summary(summary):
    streaming = summary["streaming_status"]
    lake = summary["data_lake_summary"]
    recent = summary["recent_scored"]

    print("Fraud Risk Data Lake Summary")
    print("=" * 72)
    print(f"Kafka bootstrap servers: {streaming['kafka']['bootstrap_servers']}")
    print(f"Raw topic: {streaming['kafka']['raw_topic']}")
    print(f"Scored topic: {streaming['kafka']['scored_topic']}")
    print(f"Errors topic: {streaming['kafka']['errors_topic']}")
    print("-" * 72)
    print(f"Bronze count: {lake['bronze_count']}")
    print(f"Silver count: {lake['silver_count']}")
    print(f"Gold count: {lake['gold_count']}")
    print(f"Scored decision count: {lake['scored_gold_count']}")
    print(f"Latest event timestamp: {lake.get('latest_event_timestamp') or 'not available yet'}")
    print(f"Latest ingestion timestamp: {lake.get('latest_ingestion_timestamp') or 'not available yet'}")
    print(f"Recent scored records available: {recent['total_records']}")

    if not lake["available"]:
        print("-" * 72)
        print("No Delta tables found yet.")
        print("Run these commands after Kafka has records:")
        print("scripts\\run_kafka_demo.bat")
        print("scripts\\run_spark_delta_demo.bat")


def main():
    args = parse_args()
    summary = {
        "streaming_status": get_streaming_status(),
        "data_lake_summary": get_datalake_summary(),
        "recent_scored": get_recent_scored(limit=5),
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print_human_summary(summary)


if __name__ == "__main__":
    main()
