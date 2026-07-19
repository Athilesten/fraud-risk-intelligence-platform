import argparse
import os
from pathlib import Path

from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    abs as spark_abs,
    avg,
    col,
    count,
    current_timestamp,
    from_json,
    to_timestamp,
    when,
    window,
)
from pyspark.sql.types import (
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
KAFKA_RAW_TOPIC = os.environ.get("KAFKA_RAW_TOPIC", "transactions.raw")

BRONZE_PATH = DATA_LAKE_PATH / "bronze" / "transactions_raw"
SILVER_PATH = DATA_LAKE_PATH / "silver" / "transactions_features"
GOLD_PATH = DATA_LAKE_PATH / "gold" / "fraud_risk_summary"

BRONZE_CHECKPOINT = BASE_DIR / "data" / "checkpoints" / "bronze_transactions_raw"
SILVER_CHECKPOINT = BASE_DIR / "data" / "checkpoints" / "silver_transactions_features"
GOLD_CHECKPOINT = BASE_DIR / "data" / "checkpoints" / "gold_fraud_risk_summary"


transaction_schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("event_time", StringType(), True),
    StructField("source_dataset", StringType(), True),
    StructField("step", IntegerType(), True),
    StructField("type", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("sender_id", StringType(), True),
    StructField("receiver_id", StringType(), True),
    StructField("oldbalanceOrg", DoubleType(), True),
    StructField("newbalanceOrig", DoubleType(), True),
    StructField("oldbalanceDest", DoubleType(), True),
    StructField("newbalanceDest", DoubleType(), True),
    StructField("isFlaggedFraud", IntegerType(), True),
    StructField("isFraud", IntegerType(), True),
])


def create_spark_session():
    if not (HADOOP_HOME / "bin" / "winutils.exe").exists():
        print(f"Warning: winutils.exe was not found under {HADOOP_HOME / 'bin'}.")
        print("Spark may still run, but Windows file-permission warnings can appear.")

    kafka_package = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1"

    builder = (
        SparkSession.builder
        .appName("FraudRiskBronzeSilverGoldStreaming")
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


def build_parsed_stream(spark):
    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_RAW_TOPIC)
        .option("startingOffsets", "earliest")
        .load()
    )

    return (
        kafka_df
        .selectExpr("CAST(value AS STRING) AS json_value")
        .select(from_json(col("json_value"), transaction_schema).alias("data"))
        .select("data.*")
        .withColumn("event_timestamp", to_timestamp(col("event_time")))
        .withColumn("ingestion_timestamp", current_timestamp())
    )


def build_parsed_batch(spark):
    kafka_df = (
        spark.read
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_RAW_TOPIC)
        .option("startingOffsets", "earliest")
        .option("endingOffsets", "latest")
        .load()
    )

    return (
        kafka_df
        .selectExpr("CAST(value AS STRING) AS json_value")
        .select(from_json(col("json_value"), transaction_schema).alias("data"))
        .select("data.*")
        .withColumn("event_timestamp", to_timestamp(col("event_time")))
        .withColumn("ingestion_timestamp", current_timestamp())
    )


def add_silver_features(df):
    return (
        df
        .withColumn("balance_diff_orig", col("oldbalanceOrg") - col("newbalanceOrig"))
        .withColumn("balance_diff_dest", col("newbalanceDest") - col("oldbalanceDest"))
        .withColumn("amount_to_oldbalance_ratio", col("amount") / (col("oldbalanceOrg") + 1))
        .withColumn("is_zero_balance_after_txn", when(col("newbalanceOrig") == 0, 1).otherwise(0))
        .withColumn(
            "sender_balance_mismatch",
            when(spark_abs((col("oldbalanceOrg") - col("amount")) - col("newbalanceOrig")) > 1, 1).otherwise(0),
        )
        .withColumn(
            "receiver_balance_mismatch",
            when(spark_abs((col("oldbalanceDest") + col("amount")) - col("newbalanceDest")) > 1, 1).otherwise(0),
        )
        .select(
            "event_id",
            "event_time",
            "source_dataset",
            "step",
            "type",
            "amount",
            "oldbalanceOrg",
            "newbalanceOrig",
            "oldbalanceDest",
            "newbalanceDest",
            "isFlaggedFraud",
            "isFraud",
            "balance_diff_orig",
            "balance_diff_dest",
            "amount_to_oldbalance_ratio",
            "is_zero_balance_after_txn",
            "sender_balance_mismatch",
            "receiver_balance_mismatch",
            "ingestion_timestamp",
            "event_timestamp",
        )
    )


def write_gold_batch(batch_df, batch_id):
    if batch_df.rdd.isEmpty():
        return

    by_type = (
        batch_df
        .groupBy("source_dataset", "type")
        .agg(
            count("*").alias("transaction_count"),
            avg("amount").alias("average_amount"),
            count(when(col("amount") >= 200000, True)).alias("high_amount_count"),
            count(when(col("is_zero_balance_after_txn") == 1, True)).alias("zero_balance_count"),
        )
        .withColumn("summary_level", when(col("type").isNotNull(), "source_dataset_type").otherwise("source_dataset"))
        .withColumn("window_start", current_timestamp())
        .withColumn("window_end", current_timestamp())
    )

    by_window = (
        batch_df
        .withWatermark("event_timestamp", "1 hour")
        .groupBy(window(col("event_timestamp"), "10 minutes"), "source_dataset", "type")
        .count()
        .select(
            col("source_dataset"),
            col("type"),
            col("count").alias("transaction_count"),
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
        )
        .withColumn("average_amount", col("transaction_count") * 0.0)
        .withColumn("high_amount_count", col("transaction_count") * 0)
        .withColumn("zero_balance_count", col("transaction_count") * 0)
        .withColumn("summary_level", when(col("type").isNotNull(), "window_type").otherwise("window"))
    )

    (
        by_type.unionByName(by_window)
        .withColumn("updated_at", current_timestamp())
        .write
        .format("delta")
        .mode("append")
        .save(str(GOLD_PATH))
    )


def start_delta_streams(once=False):
    spark = create_spark_session()

    if once:
        print("Spark batch validation started")
        print(f"Kafka raw topic: {KAFKA_RAW_TOPIC}")

        try:
            parsed_df = build_parsed_batch(spark)
            silver_df = add_silver_features(parsed_df)
            bronze_count = parsed_df.count()
            silver_count = silver_df.count()

            parsed_df.write.format("delta").mode("append").save(str(BRONZE_PATH))
            silver_df.write.format("delta").mode("append").save(str(SILVER_PATH))
            write_gold_batch(silver_df, 0)

            print(f"Bronze rows written: {bronze_count}")
            print(f"Silver rows written: {silver_count}")
            print(f"Gold summary path: {GOLD_PATH}")
            spark.stop()
            return 0
        except Exception as exc:
            print(f"Spark batch validation failed: {exc}")
            print("Make sure Kafka is running and topics contain records, or run the producer first.")
            spark.stop()
            return 1

    parsed_df = build_parsed_stream(spark)
    silver_df = add_silver_features(parsed_df)

    print("Spark Structured Streaming started")
    print(f"Kafka raw topic: {KAFKA_RAW_TOPIC}")
    print(f"Bronze Delta: {BRONZE_PATH}")
    print(f"Silver Delta: {SILVER_PATH}")
    print(f"Gold Delta: {GOLD_PATH}")

    bronze_writer = (
        parsed_df.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", str(BRONZE_CHECKPOINT))
    )
    if once:
        bronze_writer = bronze_writer.trigger(availableNow=True)
    bronze_query = bronze_writer.start(str(BRONZE_PATH))

    silver_writer = (
        silver_df.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", str(SILVER_CHECKPOINT))
    )
    if once:
        silver_writer = silver_writer.trigger(availableNow=True)
    silver_query = silver_writer.start(str(SILVER_PATH))

    gold_writer = (
        silver_df.writeStream
        .foreachBatch(write_gold_batch)
        .outputMode("append")
        .option("checkpointLocation", str(GOLD_CHECKPOINT))
    )
    if once:
        gold_writer = gold_writer.trigger(availableNow=True)
    gold_query = gold_writer.start()

    if once:
        print("Processing available Kafka records once.")
        bronze_query.awaitTermination()
        silver_query.awaitTermination()
        gold_query.awaitTermination()
        spark.stop()
        return 0

    print("Bronze, Silver, and Gold Delta queries are running. Press CTRL+C to stop.")
    spark.streams.awaitAnyTermination()

    bronze_query.stop()
    silver_query.stop()
    gold_query.stop()
    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="Kafka raw events to Delta bronze/silver/gold.")
    parser.add_argument("--once", action="store_true", help="Process available Kafka records and exit.")
    return parser.parse_args()


def main():
    args = parse_args()
    return start_delta_streams(once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
