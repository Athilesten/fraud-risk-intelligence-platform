import os
from datetime import datetime

import psycopg2
from psycopg2.extras import Json, RealDictCursor
from decimal import Decimal

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://fraud_user:fraud_password@localhost:5433/fraud_db"
)


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """
    Create prediction logging table if it does not exist.
    This is used by FastAPI when the app starts.
    """

    create_table_query = """
    CREATE TABLE IF NOT EXISTS fraud_predictions (
        id SERIAL PRIMARY KEY,
        step INTEGER,
        transaction_type VARCHAR(50),
        amount NUMERIC,
        oldbalance_org NUMERIC,
        newbalance_orig NUMERIC,
        oldbalance_dest NUMERIC,
        newbalance_dest NUMERIC,
        is_flagged_fraud INTEGER,
        fraud_probability NUMERIC,
        risk_level VARCHAR(50),
        alert TEXT,
        rule_risk_score INTEGER,
        rule_risk_level VARCHAR(50),
        triggered_rules TEXT,
        final_decision TEXT,
        explanation JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_query)
                conn.commit()

        print("PostgreSQL table fraud_predictions is ready.")

    except Exception as e:
        print(f"Database initialization failed: {e}")


def log_prediction(transaction, prediction, explanation=None):
    """
    Save one prediction result into PostgreSQL.
    If logging fails, API should still return prediction response.
    """

    insert_query = """
    INSERT INTO fraud_predictions (
        step,
        transaction_type,
        amount,
        oldbalance_org,
        newbalance_orig,
        oldbalance_dest,
        newbalance_dest,
        is_flagged_fraud,
        fraud_probability,
        risk_level,
        alert,
        rule_risk_score,
        rule_risk_level,
        triggered_rules,
        final_decision,
        explanation,
        created_at
    )
    VALUES (
        %(step)s,
        %(transaction_type)s,
        %(amount)s,
        %(oldbalance_org)s,
        %(newbalance_orig)s,
        %(oldbalance_dest)s,
        %(newbalance_dest)s,
        %(is_flagged_fraud)s,
        %(fraud_probability)s,
        %(risk_level)s,
        %(alert)s,
        %(rule_risk_score)s,
        %(rule_risk_level)s,
        %(triggered_rules)s,
        %(final_decision)s,
        %(explanation)s,
        %(created_at)s
    )
    RETURNING id;
    """

    values = {
        "step": transaction.get("step"),
        "transaction_type": transaction.get("type"),
        "amount": transaction.get("amount"),
        "oldbalance_org": transaction.get("oldbalanceOrg"),
        "newbalance_orig": transaction.get("newbalanceOrig"),
        "oldbalance_dest": transaction.get("oldbalanceDest"),
        "newbalance_dest": transaction.get("newbalanceDest"),
        "is_flagged_fraud": transaction.get("isFlaggedFraud"),
        "fraud_probability": prediction.get("fraud_probability"),
        "risk_level": prediction.get("risk_level"),
        "alert": prediction.get("alert"),
        "rule_risk_score": prediction.get("rule_risk_score"),
        "rule_risk_level": prediction.get("rule_risk_level"),
        "triggered_rules": " | ".join(prediction.get("triggered_rules", [])),
        "final_decision": prediction.get("final_decision"),
        "explanation": Json(explanation or {}),
        "created_at": datetime.now()
    }

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(insert_query, values)
                prediction_log_id = cur.fetchone()[0]
                conn.commit()

        return prediction_log_id

    except Exception as e:
        print(f"Prediction logging failed: {e}")
        return None
def serialize_db_value(value):
    """
    Convert PostgreSQL values into JSON-safe Python values.
    """
    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, datetime):
        return value.isoformat()

    return value


def fetch_recent_predictions(limit=50):
    """
    Fetch latest prediction logs from PostgreSQL for dashboard/API display.
    """

    query = """
    SELECT
        id,
        step,
        transaction_type,
        amount,
        fraud_probability,
        risk_level,
        rule_risk_score,
        rule_risk_level,
        final_decision,
        triggered_rules,
        created_at
    FROM fraud_predictions
    ORDER BY id DESC
    LIMIT %s;
    """

    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (limit,))
                rows = cur.fetchall()

        clean_rows = []

        for row in rows:
            clean_row = {
                key: serialize_db_value(value)
                for key, value in dict(row).items()
            }
            clean_rows.append(clean_row)

        return clean_rows

    except Exception as e:
        print(f"Fetching prediction logs failed: {e}")
        return []