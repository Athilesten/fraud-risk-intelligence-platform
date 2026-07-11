# #Read Kafka transactions
# Process with Spark
# Save raw data
# Save curated/scored-ready data

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
HADOOP_HOME = BASE_DIR / "hadoop"

os.environ["HADOOP_HOME"] = str(HADOOP_HOME)
os.environ["hadoop.home.dir"] = str(HADOOP_HOME)
os.environ["PATH"] = str(HADOOP_HOME / "bin") + os.pathsep + os.environ.get("PATH", "")
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    from_json,
    current_timestamp,
    abs as spark_abs,
    when
)
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType
)

from delta import configure_spark_with_delta_pip


# -------------------------------
# Paths
# -------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DELTA_PATH = BASE_DIR / "data" / "delta" / "raw_transactions"
CURATED_DELTA_PATH = BASE_DIR / "data" / "delta" / "curated_transactions"

RAW_CHECKPOINT_PATH = BASE_DIR / "data" / "checkpoints" / "raw_transactions"
CURATED_CHECKPOINT_PATH = BASE_DIR / "data" / "checkpoints" / "curated_transactions"


# -------------------------------
# Kafka Config
# -------------------------------

KAFKA_BOOTSTRAP_SERVER = "localhost:9092"
KAFKA_TOPIC = "transactions"


# -------------------------------
# Transaction Schema
# -------------------------------

transaction_schema = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("event_time", StringType(), True),
    StructField("step", IntegerType(), True),
    StructField("type", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("oldbalanceOrg", DoubleType(), True),
    StructField("newbalanceOrig", DoubleType(), True),
    StructField("oldbalanceDest", DoubleType(), True),
    StructField("newbalanceDest", DoubleType(), True),
    StructField("isFlaggedFraud", IntegerType(), True)
])


# -------------------------------
# Spark Session
# -------------------------------
def create_spark_session():
    kafka_package = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1"

    builder = (
        SparkSession.builder
        .appName("FraudRiskSparkStructuredStreaming")
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "2g")
    )

    spark = configure_spark_with_delta_pip(
        builder,
        extra_packages=[kafka_package]
    ).getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    return spark


# -------------------------------
# Stream Processing
# -------------------------------

def main():
    spark = create_spark_session()

    print("Spark Structured Streaming started")
    print("Reading from Kafka topic:", KAFKA_TOPIC)
    print("Raw Delta path:", RAW_DELTA_PATH)
    print("Curated Delta path:", CURATED_DELTA_PATH)

    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVER)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "earliest")
        .load()
    )

    parsed_df = (
        kafka_df
        .selectExpr("CAST(value AS STRING) as json_value")
        .select(from_json(col("json_value"), transaction_schema).alias("data"))
        .select("data.*")
        .withColumn("ingestion_timestamp", current_timestamp())
    )

    raw_query = (
        parsed_df.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", str(RAW_CHECKPOINT_PATH))
        .start(str(RAW_DELTA_PATH))
    )

    curated_df = (
        parsed_df
        .withColumn("type", col("type"))
        .withColumn("balance_diff_orig", col("oldbalanceOrg") - col("newbalanceOrig"))
        .withColumn("balance_diff_dest", col("newbalanceDest") - col("oldbalanceDest"))
        .withColumn("amount_to_oldbalance_ratio", col("amount") / (col("oldbalanceOrg") + 1))
        .withColumn(
            "is_zero_balance_after_txn",
            when(col("newbalanceOrig") == 0, 1).otherwise(0)
        )
        .withColumn(
            "sender_balance_mismatch",
            when(
                spark_abs((col("oldbalanceOrg") - col("amount")) - col("newbalanceOrig")) > 1,
                1
            ).otherwise(0)
        )
        .withColumn(
            "receiver_balance_mismatch",
            when(
                spark_abs((col("oldbalanceDest") + col("amount")) - col("newbalanceDest")) > 1,
                1
            ).otherwise(0)
        )
        .withColumn("curated_timestamp", current_timestamp())
    )

    curated_query = (
        curated_df.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", str(CURATED_CHECKPOINT_PATH))
        .start(str(CURATED_DELTA_PATH))
    )

    print("Both raw and curated Delta streaming queries are running.")
    print("Press CTRL + C to stop Spark streaming.")

    raw_query.awaitTermination()
    curated_query.awaitTermination()


if __name__ == "__main__":
    main()