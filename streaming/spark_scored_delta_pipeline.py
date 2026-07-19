import os
import argparse
from pathlib import Path

from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, from_json
from pyspark.sql.types import (
    ArrayType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)


BASE_DIR = Path(__file__).resolve().parent.parent
HADOOP_HOME = BASE_DIR / "hadoop"
DATA_LAKE_PATH = Path(os.environ.get("DATA_LAKE_PATH", BASE_DIR / "data" / "delta"))
DEFAULT_PYTHON = BASE_DIR / "venv" / "Scripts" / "python.exe"

os.environ["HADOOP_HOME"] = str(HADOOP_HOME)
os.environ["hadoop.home.dir"] = str(HADOOP_HOME)
os.environ["PATH"] = str(HADOOP_HOME / "bin") + os.pathsep + os.environ.get("PATH", "")
if DEFAULT_PYTHON.exists():
    os.environ.setdefault("PYSPARK_PYTHON", str(DEFAULT_PYTHON))
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", str(DEFAULT_PYTHON))

KAFKA_BOOTSTRAP_SERVERS = os.environ.get(
    "KAFKA_BOOTSTRAP_SERVERS",
    os.environ.get("KAFKA_BOOTSTRAP_SERVER", "localhost:9092")
)
KAFKA_SCORED_TOPIC = os.environ.get("KAFKA_SCORED_TOPIC", "transactions.scored")

SCORED_GOLD_PATH = DATA_LAKE_PATH / "gold" / "scored_fraud_decisions"
SCORED_CHECKPOINT = BASE_DIR / "data" / "checkpoints" / "gold_scored_fraud_decisions"


prediction_schema = StructType([
    StructField("fraud_probability", DoubleType(), True),
    StructField("risk_level", StringType(), True),
    StructField("alert", StringType(), True),
    StructField("rule_risk_score", IntegerType(), True),
    StructField("rule_risk_level", StringType(), True),
    StructField("triggered_rules", ArrayType(StringType()), True),
    StructField("final_decision", StringType(), True),
])

scored_schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("event_time", StringType(), True),
    StructField("source_dataset", StringType(), True),
    StructField("step", IntegerType(), True),
    StructField("type", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("oldbalanceOrg", DoubleType(), True),
    StructField("newbalanceOrig", DoubleType(), True),
    StructField("oldbalanceDest", DoubleType(), True),
    StructField("newbalanceDest", DoubleType(), True),
    StructField("isFlaggedFraud", IntegerType(), True),
    StructField("isFraud", IntegerType(), True),
    StructField("prediction_log_id", IntegerType(), True),
    StructField("scored_at", StringType(), True),
    StructField("prediction", prediction_schema, True),
])


def create_spark_session():
    if not (HADOOP_HOME / "bin" / "winutils.exe").exists():
        print(f"Warning: winutils.exe was not found under {HADOOP_HOME / 'bin'}.")
        print("Spark may still run, but Windows file-permission warnings can appear.")

    kafka_package = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1"

    builder = (
        SparkSession.builder
        .appName("FraudRiskScoredDecisionsStreaming")
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.driver.memory", "2g")
    )

    spark = configure_spark_with_delta_pip(
        builder,
        extra_packages=[kafka_package],
    ).getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def start_scored_stream(once=False):
    spark = create_spark_session()

    reader = spark.read if once else spark.readStream
    kafka_reader = (
        reader
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_SCORED_TOPIC)
        .option("startingOffsets", "earliest")
    )
    if once:
        kafka_reader = kafka_reader.option("endingOffsets", "latest")

    try:
        kafka_df = kafka_reader.load()
    except Exception as exc:
        print(f"Spark scored pipeline could not read Kafka: {exc}")
        print("Start Kafka first, create topics, and run scripts\\run_kafka_demo.bat.")
        spark.stop()
        return 1

    scored_df = (
        kafka_df
        .selectExpr("CAST(value AS STRING) AS json_value")
        .select(from_json(col("json_value"), scored_schema).alias("data"))
        .select("data.*")
        .select(
            "event_id",
            "event_time",
            "source_dataset",
            "type",
            "amount",
            col("prediction.fraud_probability").alias("fraud_probability"),
            col("prediction.risk_level").alias("risk_level"),
            col("prediction.rule_risk_score").alias("rule_risk_score"),
            col("prediction.rule_risk_level").alias("rule_risk_level"),
            col("prediction.final_decision").alias("final_decision"),
            col("prediction.triggered_rules").alias("triggered_rules"),
            "prediction_log_id",
            "scored_at",
        )
        .withColumn("ingestion_timestamp", current_timestamp())
    )

    print("Spark scored decisions pipeline started")
    print(f"Kafka scored topic: {KAFKA_SCORED_TOPIC}")
    print(f"Delta path: {SCORED_GOLD_PATH}")

    if once:
        try:
            scored_count = scored_df.count()
            scored_df.write.format("delta").mode("append").save(str(SCORED_GOLD_PATH))
            print(f"Scored decision rows written: {scored_count}")
            print(f"Delta path: {SCORED_GOLD_PATH}")
            spark.stop()
            return 0
        except Exception as exc:
            print(f"Spark scored batch validation failed: {exc}")
            print("Make sure transactions.scored has records by running scripts\\run_kafka_demo.bat first.")
            spark.stop()
            return 1

    writer = (
        scored_df.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", str(SCORED_CHECKPOINT))
    )

    query = writer.start(str(SCORED_GOLD_PATH))

    query.awaitTermination()
    spark.stop()
    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="Kafka scored events to Delta gold scored decisions.")
    parser.add_argument("--once", action="store_true", help="Process available Kafka records and exit.")
    return parser.parse_args()


def main():
    args = parse_args()
    return start_scored_stream(once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
