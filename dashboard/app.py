
import os
from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# -------------------------------
# Paths and API Config
# -------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

PROCESSED_DIR = BASE_DIR / "data" / "processed"
ALERT_LOG_PATH = PROCESSED_DIR / "fraud_alerts.csv"
BATCH_LOG_PATH = PROCESSED_DIR / "batch_predictions.csv"
REALTIME_LOG_PATH = PROCESSED_DIR / "realtime_simulation_log.csv"
KAFKA_LOG_PATH = PROCESSED_DIR / "kafka_scored_transactions.csv"
RAW_DELTA_PATH = BASE_DIR / "data" / "delta" / "raw_transactions"
CURATED_DELTA_PATH = BASE_DIR / "data" / "delta" / "curated_transactions"
HADOOP_HOME_PATH = BASE_DIR / "hadoop"
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

PREDICT_API_URL = f"{API_BASE_URL}/predict"
BATCH_API_URL = f"{API_BASE_URL}/predict_batch"
HEALTH_API_URL = f"{API_BASE_URL}/health"
LOGS_API_URL = f"{API_BASE_URL}/prediction_logs"
METRICS_API_URL = f"{API_BASE_URL}/monitoring/metrics"

API_KEY = os.environ.get("FRAUD_API_KEY", "dev_fraud_api_key_123")
API_HEADERS = {
    "X-API-Key": API_KEY
}


# -------------------------------
# Helper Functions
# -------------------------------

def save_alert_log(transaction, prediction):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    log_row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "step": transaction["step"],
        "type": transaction["type"],
        "amount": transaction["amount"],
        "oldbalanceOrg": transaction["oldbalanceOrg"],
        "newbalanceOrig": transaction["newbalanceOrig"],
        "oldbalanceDest": transaction["oldbalanceDest"],
        "newbalanceDest": transaction["newbalanceDest"],
        "isFlaggedFraud": transaction["isFlaggedFraud"],
        "fraud_probability": prediction["fraud_probability"],
        "risk_level": prediction["risk_level"],
        "alert": prediction["alert"],
        
    }

    new_df = pd.DataFrame([log_row])

    if ALERT_LOG_PATH.exists():
        old_df = pd.read_csv(ALERT_LOG_PATH)
        final_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        final_df = new_df

    final_df.to_csv(ALERT_LOG_PATH, index=False)


def load_alert_log():
    if ALERT_LOG_PATH.exists():
        return pd.read_csv(ALERT_LOG_PATH)
    return pd.DataFrame()


def save_batch_log(result_df):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    result_df = result_df.copy()
    result_df["batch_saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if BATCH_LOG_PATH.exists():
        old_df = pd.read_csv(BATCH_LOG_PATH)
        final_df = pd.concat([old_df, result_df], ignore_index=True)
    else:
        final_df = result_df

    final_df.to_csv(BATCH_LOG_PATH, index=False)


def load_batch_log():
    if BATCH_LOG_PATH.exists():
        return pd.read_csv(BATCH_LOG_PATH)
    return pd.DataFrame()

def load_realtime_log():
    if REALTIME_LOG_PATH.exists():
        return pd.read_csv(REALTIME_LOG_PATH)
    return pd.DataFrame()

def load_kafka_log():
    if KAFKA_LOG_PATH.exists():
        return pd.read_csv(KAFKA_LOG_PATH)
    return pd.DataFrame()

@st.cache_data(ttl=60)
def load_delta_table_as_pandas(delta_path_str, limit_rows=100):
    delta_path = Path(delta_path_str)

    if not delta_path.exists():
        return {
            "exists": False,
            "error": None,
            "count": 0,
            "data": pd.DataFrame()
        }

    try:
        from pyspark.sql import SparkSession
        from pyspark.sql.functions import col
        from delta import configure_spark_with_delta_pip

        os.environ["HADOOP_HOME"] = str(HADOOP_HOME_PATH)
        os.environ["hadoop.home.dir"] = str(HADOOP_HOME_PATH)
        os.environ["PATH"] = str(HADOOP_HOME_PATH / "bin") + os.pathsep + os.environ.get("PATH", "")

        builder = (
            SparkSession.builder
            .appName("StreamlitDeltaLakeMonitoring")
            .master("local[*]")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .config("spark.sql.shuffle.partitions", "2")
            .config("spark.driver.memory", "2g")
        )

        spark = configure_spark_with_delta_pip(builder).getOrCreate()
        spark.sparkContext.setLogLevel("WARN")

        df = spark.read.format("delta").load(str(delta_path))

        total_count = df.count()

        sort_column = None

        for candidate_column in ["curated_timestamp", "ingestion_timestamp", "event_time"]:
            if candidate_column in df.columns:
                sort_column = candidate_column
                break

        if sort_column:
            display_df = df.orderBy(col(sort_column).desc()).limit(limit_rows)
        else:
            display_df = df.limit(limit_rows)

        pandas_df = display_df.toPandas()

        return {
            "exists": True,
            "error": None,
            "count": total_count,
            "data": pandas_df
        }

    except Exception as e:
        return {
            "exists": True,
            "error": str(e),
            "count": 0,
            "data": pd.DataFrame()
        }

def check_api_health():
    try:
       response = requests.get(HEALTH_API_URL, timeout=3)
       return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


# -------------------------------
# Page Config
# -------------------------------

st.set_page_config(
    page_title="Fraud Risk Intelligence Dashboard",
    page_icon="🚨",
    layout="wide",
)

st.title("🚨 Real-Time Fraud Detection and Risk Intelligence Platform")

st.markdown(
    """
    This dashboard scores transactions using a machine learning model,
    stores fraud alerts, and supports batch CSV fraud prediction.
    """
)

api_running = check_api_health()

if api_running:
    st.success("FastAPI server is running.")
else:
    st.error("FastAPI server is not running. Run this command first: uvicorn api.main:app --reload")


# -------------------------------
# Sidebar Transaction Input
# -------------------------------

st.sidebar.header("Single Transaction Input")

step = st.sidebar.number_input(
    "Step / Time Unit",
    min_value=1,
    value=1,
    key="single_step_input",
)

txn_type = st.sidebar.selectbox(
    "Transaction Type",
    ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"],
    key="single_type_input",
)

amount = st.sidebar.number_input(
    "Transaction Amount",
    min_value=0.0,
    value=95000.0,
    key="single_amount_input",
)

oldbalanceOrg = st.sidebar.number_input(
    "Sender Old Balance",
    min_value=0.0,
    value=100000.0,
    key="single_oldbalance_org_input",
)

newbalanceOrig = st.sidebar.number_input(
    "Sender New Balance",
    min_value=0.0,
    value=5000.0,
    key="single_newbalance_orig_input",
)

oldbalanceDest = st.sidebar.number_input(
    "Receiver Old Balance",
    min_value=0.0,
    value=0.0,
    key="single_oldbalance_dest_input",
)

newbalanceDest = st.sidebar.number_input(
    "Receiver New Balance",
    min_value=0.0,
    value=95000.0,
    key="single_newbalance_dest_input",
)

isFlaggedFraud = st.sidebar.selectbox(
    "System Flagged Fraud?",
    [0, 1],
    key="single_flagged_input",
)

transaction = {
    "step": int(step),
    "type": txn_type,
    "amount": float(amount),
    "oldbalanceOrg": float(oldbalanceOrg),
    "newbalanceOrig": float(newbalanceOrig),
    "oldbalanceDest": float(oldbalanceDest),
    "newbalanceDest": float(newbalanceDest),
    "isFlaggedFraud": int(isFlaggedFraud),
}


# -------------------------------
# Single Prediction Section
# -------------------------------

st.subheader("Single Transaction Fraud Prediction")

col1, col2 = st.columns([1, 1])

with col1:
    st.write("Transaction Details")
    st.json(transaction)

with col2:
    st.write("Fraud Risk Prediction")

    if st.button("Predict Fraud Risk", key="single_prediction_button"):
        try:
            response = requests.post(PREDICT_API_URL, json=transaction,headers=API_HEADERS,
 timeout=30)

            if response.status_code == 200:
                result = response.json()
                prediction = result["prediction"]
                explanation = result.get("explanation", {})

                save_alert_log(transaction, prediction)

                fraud_probability = prediction["fraud_probability"]
                risk_level = prediction["risk_level"]
                alert = prediction["alert"]
                rule_risk_score = prediction.get("rule_risk_score", 0)
                rule_risk_level = prediction.get("rule_risk_level", "LOW")
                triggered_rules = prediction.get("triggered_rules", [])
                final_decision = prediction.get("final_decision", "APPROVE")

                st.metric(
                    label="Fraud Probability",
                    value=f"{fraud_probability * 100:.2f}%",
                )

                if risk_level == "HIGH":
                    st.error(f"Risk Level: {risk_level}")
                    st.error(alert)
                elif risk_level == "MEDIUM":
                    st.warning(f"Risk Level: {risk_level}")
                    st.warning(alert)
                else:
                    st.success(f"Risk Level: {risk_level}")
                    st.success(alert)
                st.metric(
                    label="Rule Risk Score",
                    value=f"{rule_risk_score}/100"
                )

                if rule_risk_level == "HIGH":
                    st.error(f"Rule Risk Level: {rule_risk_level}")
                elif rule_risk_level == "MEDIUM":
                    st.warning(f"Rule Risk Level: {rule_risk_level}")
                else:
                    st.success(f"Rule Risk Level: {rule_risk_level}")

                st.subheader("Triggered Fraud Rules")

                if triggered_rules:
                    for rule in triggered_rules:
                        st.write(f"⚠️ {rule}")
                else:
                    st.write("No fraud rules triggered.")

                st.subheader("Final Decision")

                if final_decision == "BLOCK / MANUAL REVIEW":
                    st.error(final_decision)
                elif final_decision == "MANUAL REVIEW":
                    st.warning(final_decision)
                else:
                    st.success(final_decision)
                st.subheader("Model Explanation")

                explanation_method = explanation.get("explanation_method", "Not available")
                top_features = explanation.get("top_features", [])

                st.write(f"Explanation Method: {explanation_method}")

                if top_features:
                    explanation_df = pd.DataFrame(top_features)
                    st.dataframe(explanation_df, use_container_width=True)

                    fig_explanation = px.bar(
                        explanation_df,
                        x="feature",
                        y="impact_score",
                        title="Top Features Influencing Fraud Prediction"
                    )

                    st.plotly_chart(fig_explanation, use_container_width=True)

                else:
                    st.warning("No explanation available.")

                risk_df = pd.DataFrame(
                    {
                        "Risk": ["Fraud Probability", "Safe Probability"],
                        "Value": [fraud_probability, 1 - fraud_probability],
                    }
                )

                fig = px.pie(
                    risk_df,
                    names="Risk",
                    values="Value",
                    title="Fraud vs Safe Probability",
                )

                st.plotly_chart(fig, use_container_width=True)

                st.success("Single prediction saved to fraud alert log.")

            else:
                st.error("API Error")
                st.write(response.json())

        except requests.exceptions.ConnectionError:
            st.error("FastAPI server is not running.")

        except Exception as e:
            st.error(f"Something went wrong: {e}")


# -------------------------------
# Analyst Interpretation
# -------------------------------

st.divider()

st.subheader("Analyst Interpretation")

balance_diff_orig = oldbalanceOrg - newbalanceOrig
balance_diff_dest = newbalanceDest - oldbalanceDest
amount_ratio = amount / (oldbalanceOrg + 1)

analysis_data = {
    "Amount": amount,
    "Sender Balance Difference": balance_diff_orig,
    "Receiver Balance Difference": balance_diff_dest,
    "Amount to Sender Old Balance Ratio": amount_ratio,
    "Sender Zero Balance After Transaction": "Yes" if newbalanceOrig == 0 else "No",
}

st.dataframe(pd.DataFrame([analysis_data]), use_container_width=True)

st.info(
    """
    Fraud risk usually increases when the transaction amount is high,
    sender balance becomes zero after transfer, or balance movement does not match the transaction amount.
    """
)


# -------------------------------
# Fraud Alert History
# -------------------------------

st.divider()

st.subheader("Single Transaction Alert History")

alert_df = load_alert_log()

if alert_df.empty:
    st.warning("No single transaction predictions logged yet.")
else:
    total_predictions = len(alert_df)
    high_risk_count = len(alert_df[alert_df["risk_level"] == "HIGH"])
    medium_risk_count = len(alert_df[alert_df["risk_level"] == "MEDIUM"])
    low_risk_count = len(alert_df[alert_df["risk_level"] == "LOW"])

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Total Predictions", total_predictions)
    m2.metric("High Risk", high_risk_count)
    m3.metric("Medium Risk", medium_risk_count)
    m4.metric("Low Risk", low_risk_count)

    st.write("Latest Single Prediction Logs")

    st.dataframe(
        alert_df.sort_values("timestamp", ascending=False),
        use_container_width=True,
    )

    risk_counts = alert_df["risk_level"].value_counts().reset_index()
    risk_counts.columns = ["Risk Level", "Count"]

    fig_risk = px.bar(
        risk_counts,
        x="Risk Level",
        y="Count",
        title="Single Prediction Risk Level Distribution",
    )

    st.plotly_chart(fig_risk, use_container_width=True)

    single_csv = alert_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Single Alert Log CSV",
        data=single_csv,
        file_name="fraud_alert_log.csv",
        mime="text/csv",
        key="download_single_alert_log",
    )


# -------------------------------
# Batch CSV Prediction
# -------------------------------

st.divider()

st.subheader("Batch Prediction: Upload Transaction CSV")

st.markdown(
    """
    Upload a PaySim-style CSV file and score multiple transactions at once.
    """
)

required_columns = [
    "step",
    "type",
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
]

st.write("Required columns:")
st.code(", ".join(required_columns))

batch_uploaded_file = st.file_uploader(
    "Upload CSV for Batch Fraud Prediction",
    type=["csv"],
    key="batch_csv_uploader_unique_final",
)

if batch_uploaded_file is not None:
    try:
        df = pd.read_csv(batch_uploaded_file)

        st.write("Uploaded Dataset Preview")
        st.dataframe(df.head(), use_container_width=True)

        st.write("Dataset Shape:", df.shape)

        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"Missing required columns: {missing_columns}")

        else:
            if "isFlaggedFraud" not in df.columns:
                df["isFlaggedFraud"] = 0

            model_input_columns = [
                "step",
                "type",
                "amount",
                "oldbalanceOrg",
                "newbalanceOrig",
                "oldbalanceDest",
                "newbalanceDest",
                "isFlaggedFraud",
            ]

            input_df = df[model_input_columns].copy()

            input_df["type"] = input_df["type"].astype(str).str.strip().str.upper()

            numeric_columns = [
                "step",
                "amount",
                "oldbalanceOrg",
                "newbalanceOrig",
                "oldbalanceDest",
                "newbalanceDest",
                "isFlaggedFraud",
            ]

            for col in numeric_columns:
                input_df[col] = pd.to_numeric(input_df[col], errors="coerce")

            before_drop = len(input_df)
            input_df = input_df.dropna()
            after_drop = len(input_df)

            if before_drop != after_drop:
                st.warning(f"Removed {before_drop - after_drop} rows because they had invalid numeric values.")

            input_df["step"] = input_df["step"].astype(int)
            input_df["isFlaggedFraud"] = input_df["isFlaggedFraud"].astype(int)

            if input_df.empty:
                st.error("No valid rows available for prediction.")
            else:
                max_rows_allowed = min(1000, len(input_df))

                max_rows = st.number_input(
                    "Number of rows to score",
                    min_value=1,
                    max_value=max_rows_allowed,
                    value=min(100, max_rows_allowed),
                    key="batch_rows_number_input_unique_final",
                )

                input_df = input_df.head(int(max_rows))

                st.write("Rows Selected for Prediction")
                st.dataframe(input_df.head(), use_container_width=True)

                if st.button("Run Batch Prediction", key="run_batch_prediction_button_unique_final"):
                    try:
                        payload = {
                            "transactions": input_df.to_dict(orient="records")
                        }

                        response = requests.post(
                            BATCH_API_URL,
                            json=payload,
   			    headers=API_HEADERS, 			    timeout=120,
                        )

                        if response.status_code == 200:
                            result = response.json()

                            result_df = pd.DataFrame(result["results"])

                            save_batch_log(result_df)

                            st.success(
                                f"Batch prediction completed and saved for {result['total_transactions']} transactions."
                            )

                            st.subheader("Batch Prediction Results")
                            st.dataframe(result_df, use_container_width=True)

                            high_risk = len(result_df[result_df["risk_level"] == "HIGH"])
                            medium_risk = len(result_df[result_df["risk_level"] == "MEDIUM"])
                            low_risk = len(result_df[result_df["risk_level"] == "LOW"])

                            b1, b2, b3 = st.columns(3)
                            b1.metric("High Risk", high_risk)
                            b2.metric("Medium Risk", medium_risk)
                            b3.metric("Low Risk", low_risk)

                            risk_counts = result_df["risk_level"].value_counts().reset_index()
                            risk_counts.columns = ["Risk Level", "Count"]

                            fig_batch_risk = px.bar(
                                risk_counts,
                                x="Risk Level",
                                y="Count",
                                title="Batch Risk Level Distribution",
                            )

                            st.plotly_chart(fig_batch_risk, use_container_width=True)

                            avg_risk_type = (
                                result_df.groupby("type")["fraud_probability"]
                                .mean()
                                .reset_index()
                            )

                            fig_avg_type = px.bar(
                                avg_risk_type,
                                x="type",
                                y="fraud_probability",
                                title="Average Fraud Probability by Transaction Type",
                            )

                            st.plotly_chart(fig_avg_type, use_container_width=True)

                            batch_csv = result_df.to_csv(index=False).encode("utf-8")

                            st.download_button(
                                label="Download Current Batch Prediction CSV",
                                data=batch_csv,
                                file_name="batch_fraud_predictions.csv",
                                mime="text/csv",
                                key="download_current_batch_csv_unique_final",
                            )

                        else:
                            st.error("Batch API Error")
                            st.write(response.json())

                    except requests.exceptions.ConnectionError:
                        st.error("FastAPI server is not running.")

                    except Exception as e:
                        st.error(f"Something went wrong during batch prediction: {e}")

    except Exception as e:
        st.error(f"Could not read uploaded CSV file: {e}")


# -------------------------------
# Saved Batch Prediction History
# -------------------------------

st.divider()

st.subheader("Saved Batch Prediction History")

batch_log_df = load_batch_log()

if batch_log_df.empty:
    st.warning("No batch predictions saved yet.")
else:
    st.write("Saved Batch Prediction Records")

    if "batch_saved_at" in batch_log_df.columns:
        batch_log_display = batch_log_df.sort_values("batch_saved_at", ascending=False)
    else:
        batch_log_display = batch_log_df

    st.dataframe(batch_log_display, use_container_width=True)

    total_batch_records = len(batch_log_df)
    high_batch = len(batch_log_df[batch_log_df["risk_level"] == "HIGH"])
    medium_batch = len(batch_log_df[batch_log_df["risk_level"] == "MEDIUM"])
    low_batch = len(batch_log_df[batch_log_df["risk_level"] == "LOW"])

    h1, h2, h3, h4 = st.columns(4)

    h1.metric("Total Batch Records", total_batch_records)
    h2.metric("High Risk", high_batch)
    h3.metric("Medium Risk", medium_batch)
    h4.metric("Low Risk", low_batch)

    batch_risk_counts = batch_log_df["risk_level"].value_counts().reset_index()
    batch_risk_counts.columns = ["Risk Level", "Count"]

    fig_saved_batch = px.bar(
        batch_risk_counts,
        x="Risk Level",
        y="Count",
        title="Saved Batch Prediction Risk Distribution",
    )

    st.plotly_chart(fig_saved_batch, use_container_width=True)

    saved_batch_csv = batch_log_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Saved Batch Prediction History",
        data=saved_batch_csv,
        file_name="saved_batch_prediction_history.csv",
        mime="text/csv",
        key="download_saved_batch_history_unique_final",
    )



# -------------------------------
# Real-Time Simulation Monitoring
# -------------------------------

st.divider()

st.subheader("Real-Time Transaction Simulation Monitoring")

st.markdown(
    """
    This section displays transactions generated by the real-time simulator.
    Run `python streaming/transaction_simulator.py` to generate new live-style transaction events.
    """
)

realtime_df = load_realtime_log()

refresh_col1, refresh_col2 = st.columns([1, 4])

with refresh_col1:
    if st.button("Refresh Real-Time Log", key="refresh_realtime_log_button"):
        st.rerun()

if realtime_df.empty:
    st.warning("No real-time simulation records found yet.")
    st.info("Run this command in another terminal: python streaming/transaction_simulator.py")

else:
    total_realtime = len(realtime_df)

    approved_count = len(realtime_df[realtime_df["final_decision"] == "APPROVE"])
    manual_review_count = len(realtime_df[realtime_df["final_decision"] == "MANUAL REVIEW"])
    block_count = len(realtime_df[realtime_df["final_decision"] == "BLOCK / MANUAL REVIEW"])

    r1, r2, r3, r4 = st.columns(4)

    r1.metric("Total Simulated Transactions", total_realtime)
    r2.metric("Approved", approved_count)
    r3.metric("Manual Review", manual_review_count)
    r4.metric("Blocked / Review", block_count)

    st.write("Latest Real-Time Transactions")

    if "timestamp" in realtime_df.columns:
        realtime_display_df = realtime_df.sort_values("timestamp", ascending=False)
    else:
        realtime_display_df = realtime_df

    st.dataframe(
        realtime_display_df,
        use_container_width=True
    )

    if "final_decision" in realtime_df.columns:
        decision_counts = realtime_df["final_decision"].value_counts().reset_index()
        decision_counts.columns = ["Final Decision", "Count"]

        fig_decision = px.bar(
            decision_counts,
            x="Final Decision",
            y="Count",
            title="Final Decision Distribution"
        )

        st.plotly_chart(fig_decision, use_container_width=True)

    if "rule_risk_level" in realtime_df.columns:
        rule_risk_counts = realtime_df["rule_risk_level"].value_counts().reset_index()
        rule_risk_counts.columns = ["Rule Risk Level", "Count"]

        fig_rule_risk = px.bar(
            rule_risk_counts,
            x="Rule Risk Level",
            y="Count",
            title="Rule Risk Level Distribution"
        )

        st.plotly_chart(fig_rule_risk, use_container_width=True)

    if "type" in realtime_df.columns and "fraud_probability" in realtime_df.columns:
        avg_realtime_risk = (
            realtime_df.groupby("type")["fraud_probability"]
            .mean()
            .reset_index()
        )

        fig_avg_realtime = px.bar(
            avg_realtime_risk,
            x="type",
            y="fraud_probability",
            title="Average Fraud Probability by Transaction Type"
        )

        st.plotly_chart(fig_avg_realtime, use_container_width=True)

    realtime_csv = realtime_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Real-Time Simulation Log",
        data=realtime_csv,
        file_name="realtime_simulation_log.csv",
        mime="text/csv",
        key="download_realtime_simulation_log_button"
    )
# -------------------------------
# Kafka Streaming Monitoring
# -------------------------------

st.divider()

st.subheader("Kafka Streaming Transaction Monitoring")

st.markdown(
    """
    This section displays transactions that came through Kafka producer and Kafka consumer.
    The consumer scores each transaction using FastAPI, ML model, and rules engine.
    """
)

kafka_df = load_kafka_log()

if st.button("Refresh Kafka Log", key="refresh_kafka_log_button_unique"):
    st.rerun()

if kafka_df.empty:
    st.warning("No Kafka scored transactions found yet.")
    st.info(
        """
        Run these commands:
        
        1. Start Kafka:
        docker compose up -d
        
        2. Start FastAPI:
        uvicorn api.main:app --reload
        
        3. Start Kafka Consumer:
        python streaming/kafka_consumer.py
        
        4. Start Kafka Producer:
        python streaming/kafka_producer.py
        """
    )

else:
    total_kafka = len(kafka_df)

    approved_count = len(kafka_df[kafka_df["final_decision"] == "APPROVE"])
    manual_review_count = len(kafka_df[kafka_df["final_decision"] == "MANUAL REVIEW"])
    blocked_count = len(kafka_df[kafka_df["final_decision"] == "BLOCK / MANUAL REVIEW"])

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Total Kafka Transactions", total_kafka)
    k2.metric("Approved", approved_count)
    k3.metric("Manual Review", manual_review_count)
    k4.metric("Blocked / Review", blocked_count)

    st.write("Latest Kafka Scored Transactions")

    if "scored_at" in kafka_df.columns:
        kafka_display_df = kafka_df.sort_values("scored_at", ascending=False)
    else:
        kafka_display_df = kafka_df

    st.dataframe(kafka_display_df, use_container_width=True)

    if "final_decision" in kafka_df.columns:
        decision_counts = kafka_df["final_decision"].value_counts().reset_index()
        decision_counts.columns = ["Final Decision", "Count"]

        fig_decision = px.bar(
            decision_counts,
            x="Final Decision",
            y="Count",
            title="Kafka Final Decision Distribution"
        )

        st.plotly_chart(fig_decision, use_container_width=True)

    if "ml_risk_level" in kafka_df.columns:
        ml_risk_counts = kafka_df["ml_risk_level"].value_counts().reset_index()
        ml_risk_counts.columns = ["ML Risk Level", "Count"]

        fig_ml_risk = px.bar(
            ml_risk_counts,
            x="ML Risk Level",
            y="Count",
            title="Kafka ML Risk Level Distribution"
        )

        st.plotly_chart(fig_ml_risk, use_container_width=True)

    if "rule_risk_level" in kafka_df.columns:
        rule_risk_counts = kafka_df["rule_risk_level"].value_counts().reset_index()
        rule_risk_counts.columns = ["Rule Risk Level", "Count"]

        fig_rule_risk = px.bar(
            rule_risk_counts,
            x="Rule Risk Level",
            y="Count",
            title="Kafka Rule Risk Level Distribution"
        )

        st.plotly_chart(fig_rule_risk, use_container_width=True)

    if "type" in kafka_df.columns and "fraud_probability" in kafka_df.columns:
        avg_kafka_risk = (
            kafka_df.groupby("type")["fraud_probability"]
            .mean()
            .reset_index()
        )

        fig_avg_kafka = px.bar(
            avg_kafka_risk,
            x="type",
            y="fraud_probability",
            title="Average Kafka Fraud Probability by Transaction Type"
        )

        st.plotly_chart(fig_avg_kafka, use_container_width=True)

    kafka_csv = kafka_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Kafka Scored Transactions",
        data=kafka_csv,
        file_name="kafka_scored_transactions.csv",
        mime="text/csv",
        key="download_kafka_scored_transactions_unique"
    )
    # -------------------------------
# API Monitoring Metrics
# -------------------------------

st.header("API Monitoring Metrics")

st.write(
    "This section shows request count, error count, and latency metrics from the FastAPI service."
)

if st.button("Load API Monitoring Metrics"):
    try:
        response = requests.get(
            METRICS_API_URL,
            headers=API_HEADERS,
            timeout=10
        )

        response.raise_for_status()

        metrics_data = response.json()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Requests", metrics_data.get("total_requests", 0))
        col2.metric("Total Errors", metrics_data.get("total_errors", 0))
        col3.metric(
            "Avg Latency",
            f"{metrics_data.get('avg_latency_ms', 0)} ms"
        )
        col4.metric(
            "Max Latency",
            f"{metrics_data.get('max_latency_ms', 0)} ms"
        )

        endpoint_data = metrics_data.get("by_endpoint", [])

        if endpoint_data:
            endpoint_df = pd.DataFrame(endpoint_data)

            st.subheader("Endpoint-wise API Metrics")
            st.dataframe(endpoint_df, use_container_width=True)

            fig = px.bar(
                endpoint_df,
                x="endpoint",
                y="avg_latency_ms",
                title="Average Latency by Endpoint"
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No endpoint metrics available yet.")

    except Exception as e:
        st.error(f"Failed to load API monitoring metrics: {e}")      
# -------------------------------
# PostgreSQL Prediction Logs
# -------------------------------

st.header("PostgreSQL Prediction Logs")

st.write(
    "This section shows the latest fraud prediction records saved in PostgreSQL."
)

log_limit = st.slider(
    "Number of latest prediction logs",
    min_value=5,
    max_value=100,
    value=20,
    step=5
)

if st.button("Load PostgreSQL Prediction Logs"):
    try:
        response = requests.get(
            f"{LOGS_API_URL}?limit={log_limit}",
            headers=API_HEADERS,
	    timeout=10
        )

        response.raise_for_status()

        logs_data = response.json()
        logs = logs_data.get("logs", [])

        if not logs:
            st.info("No prediction logs found yet. Run one prediction first.")
        else:
            logs_df = pd.DataFrame(logs)

            logs_df["fraud_probability"] = pd.to_numeric(
                logs_df["fraud_probability"],
                errors="coerce"
            )

            logs_df["amount"] = pd.to_numeric(
                logs_df["amount"],
                errors="coerce"
            )

            total_logs = len(logs_df)
            high_risk_count = (logs_df["risk_level"] == "HIGH").sum()
            manual_review_count = (
                logs_df["final_decision"].astype(str).str.contains(
                    "MANUAL REVIEW",
                    case=False,
                    na=False
                )
            ).sum()

            average_probability = logs_df["fraud_probability"].mean()

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Logs Loaded", total_logs)
            col2.metric("High Risk", int(high_risk_count))
            col3.metric("Manual Review", int(manual_review_count))
            col4.metric("Avg Fraud Probability", f"{average_probability:.4f}")

            st.subheader("Latest PostgreSQL Prediction Records")

            st.dataframe(
                logs_df,
                use_container_width=True
            )

            if "risk_level" in logs_df.columns:
                st.subheader("Risk Level Distribution")

                risk_counts = logs_df["risk_level"].value_counts().reset_index()
                risk_counts.columns = ["risk_level", "count"]

                fig = px.bar(
                    risk_counts,
                    x="risk_level",
                    y="count",
                    title="Prediction Logs by Risk Level"
                )

                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to load PostgreSQL prediction logs: {e}")

   
    # -------------------------------
# Delta Lake Storage Monitoring
# -------------------------------

st.divider()

st.subheader("Delta Lake Storage Monitoring")

st.markdown(
    """
    This section reads Spark Delta Lake tables created from Kafka streaming.
    
    Raw Delta table stores original Kafka transactions.
    Curated Delta table stores cleaned transactions with engineered fraud-risk features.
    """
)

if st.button("Load / Refresh Delta Lake Tables", key="load_delta_lake_tables_button"):
    st.session_state["load_delta_tables"] = True

if st.session_state.get("load_delta_tables", False):

    with st.spinner("Loading Delta Lake tables using Spark..."):
        raw_delta_result = load_delta_table_as_pandas(
            str(RAW_DELTA_PATH),
            limit_rows=100
        )

        curated_delta_result = load_delta_table_as_pandas(
            str(CURATED_DELTA_PATH),
            limit_rows=100
        )

    if not raw_delta_result["exists"]:
        st.warning("Raw Delta table not found yet.")
        st.info("Run Spark streaming and Kafka producer first.")

    if not curated_delta_result["exists"]:
        st.warning("Curated Delta table not found yet.")
        st.info("Run Spark streaming and Kafka producer first.")

    if raw_delta_result["error"]:
        st.error("Error while reading Raw Delta table.")
        st.write(raw_delta_result["error"])

    if curated_delta_result["error"]:
        st.error("Error while reading Curated Delta table.")
        st.write(curated_delta_result["error"])

    if (
        raw_delta_result["exists"]
        and curated_delta_result["exists"]
        and raw_delta_result["error"] is None
        and curated_delta_result["error"] is None
    ):
        raw_delta_df = raw_delta_result["data"]
        curated_delta_df = curated_delta_result["data"]

        d1, d2, d3 = st.columns(3)

        d1.metric(
            "Raw Delta Transactions",
            raw_delta_result["count"]
        )

        d2.metric(
            "Curated Delta Transactions",
            curated_delta_result["count"]
        )

        d3.metric(
            "Latest Rows Displayed",
            len(curated_delta_df)
        )

        st.subheader("Latest Raw Delta Transactions")
        st.dataframe(raw_delta_df, use_container_width=True)

        st.subheader("Latest Curated Delta Transactions")
        st.dataframe(curated_delta_df, use_container_width=True)

        if not curated_delta_df.empty and "type" in curated_delta_df.columns and "amount" in curated_delta_df.columns:
            avg_amount_by_type = (
                curated_delta_df.groupby("type")["amount"]
                .mean()
                .reset_index()
            )

            fig_delta_amount = px.bar(
                avg_amount_by_type,
                x="type",
                y="amount",
                title="Average Transaction Amount by Type from Curated Delta Table"
            )

            st.plotly_chart(fig_delta_amount, use_container_width=True)

        risk_feature_columns = [
            "balance_diff_orig",
            "balance_diff_dest",
            "amount_to_oldbalance_ratio",
            "is_zero_balance_after_txn",
            "sender_balance_mismatch",
            "receiver_balance_mismatch"
        ]

        available_risk_columns = [
            col for col in risk_feature_columns
            if col in curated_delta_df.columns
        ]

        if available_risk_columns:
            st.subheader("Curated Fraud-Risk Feature Summary")

            feature_summary = (
                curated_delta_df[available_risk_columns]
                .mean(numeric_only=True)
                .reset_index()
            )

            feature_summary.columns = ["Feature", "Average Value"]

            st.dataframe(feature_summary, use_container_width=True)

            fig_feature_summary = px.bar(
                feature_summary,
                x="Feature",
                y="Average Value",
                title="Average Fraud-Risk Engineered Features from Delta Lake"
            )

            st.plotly_chart(fig_feature_summary, use_container_width=True)

else:
    st.info("Click the button above to load Delta Lake monitoring data.")