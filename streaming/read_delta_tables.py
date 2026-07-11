import os
from pathlib import Path

from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip


# -------------------------------
# Windows Hadoop Setup
# -------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

HADOOP_HOME = BASE_DIR / "hadoop"

os.environ["HADOOP_HOME"] = str(HADOOP_HOME)
os.environ["hadoop.home.dir"] = str(HADOOP_HOME)
os.environ["PATH"] = str(HADOOP_HOME / "bin") + os.pathsep + os.environ.get("PATH", "")


# -------------------------------
# Delta Paths
# -------------------------------

RAW_DELTA_PATH = BASE_DIR / "data" / "delta" / "raw_transactions"
CURATED_DELTA_PATH = BASE_DIR / "data" / "delta" / "curated_transactions"


# -------------------------------
# Spark Session
# -------------------------------

def create_spark_session():
    builder = (
        SparkSession.builder
        .appName("ReadFraudDeltaTables")
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.driver.memory", "2g")
    )

    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    return spark


# -------------------------------
# Main
# -------------------------------

def main():
    spark = create_spark_session()

    print("\nRaw Delta Path:")
    print(RAW_DELTA_PATH)

    print("\nCurated Delta Path:")
    print(CURATED_DELTA_PATH)

    if not RAW_DELTA_PATH.exists():
        print("\nRaw Delta table does not exist yet.")
        print("First run spark_streaming_delta.py and kafka_producer.py.")
        spark.stop()
        return

    if not CURATED_DELTA_PATH.exists():
        print("\nCurated Delta table does not exist yet.")
        print("First run spark_streaming_delta.py and kafka_producer.py.")
        spark.stop()
        return

    print("\nReading Raw Delta Table")
    raw_df = spark.read.format("delta").load(str(RAW_DELTA_PATH))
    raw_df.show(10, truncate=False)
    raw_df.printSchema()

    print("\nReading Curated Delta Table")
    curated_df = spark.read.format("delta").load(str(CURATED_DELTA_PATH))
    curated_df.show(10, truncate=False)
    curated_df.printSchema()

    print("\nRaw count:", raw_df.count())
    print("Curated count:", curated_df.count())

    spark.stop()


if __name__ == "__main__":
    main()