from pathlib import Path
import pandas as pd
import joblib

from feature_engineering import add_features
from rules_engine import evaluate_rules


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "models" / "fraud_model.pkl"
ENCODER_PATH = BASE_DIR / "models" / "label_encoder.pkl"

model = joblib.load(MODEL_PATH)
label_encoder = joblib.load(ENCODER_PATH)


def decide_final_action(ml_risk_level, rule_risk_level, fraud_probability, rule_risk_score):
    """
    Combine ML model risk and rule engine risk.
    """

    if ml_risk_level == "HIGH" or rule_risk_level == "HIGH":
        return "BLOCK / MANUAL REVIEW"

    if fraud_probability >= 0.50 or rule_risk_score >= 40:
        return "MANUAL REVIEW"

    return "APPROVE"


def predict_fraud(transaction):
    df = pd.DataFrame([transaction])

    txn_type = str(df.loc[0, "type"]).upper()
    df.loc[0, "type"] = txn_type

    if txn_type not in label_encoder.classes_:
        raise ValueError(
            f"Invalid transaction type: {txn_type}. "
            f"Allowed types are: {list(label_encoder.classes_)}"
        )

    # Rule engine prediction
    rule_result = evaluate_rules(transaction)

    # ML model prediction
    df["type"] = label_encoder.transform(df["type"])

    df = add_features(df)

    fraud_probability = model.predict_proba(df)[0][1]

    if fraud_probability >= 0.80:
        ml_risk_level = "HIGH"
        alert = "Fraud suspected"
    elif fraud_probability >= 0.50:
        ml_risk_level = "MEDIUM"
        alert = "Manual review required"
    else:
        ml_risk_level = "LOW"
        alert = "Transaction looks normal"

    final_decision = decide_final_action(
        ml_risk_level=ml_risk_level,
        rule_risk_level=rule_result["rule_risk_level"],
        fraud_probability=fraud_probability,
        rule_risk_score=rule_result["rule_risk_score"]
    )

    return {
        "fraud_probability": round(float(fraud_probability), 4),
        "risk_level": ml_risk_level,
        "alert": alert,
        "rule_risk_score": rule_result["rule_risk_score"],
        "rule_risk_level": rule_result["rule_risk_level"],
        "triggered_rules": rule_result["triggered_rules"],
        "final_decision": final_decision
    }


def predict_batch(transactions):
    results = []

    for transaction in transactions:
        prediction = predict_fraud(transaction)

        result_row = {
            **transaction,
            "fraud_probability": prediction["fraud_probability"],
            "risk_level": prediction["risk_level"],
            "alert": prediction["alert"],
            "rule_risk_score": prediction["rule_risk_score"],
            "rule_risk_level": prediction["rule_risk_level"],
            "triggered_rules": " | ".join(prediction["triggered_rules"]),
            "final_decision": prediction["final_decision"]
        }

        results.append(result_row)

    return results


if __name__ == "__main__":
    sample_transaction = {
        "step": 1,
        "type": "TRANSFER",
        "amount": 250000,
        "oldbalanceOrg": 250000,
        "newbalanceOrig": 0,
        "oldbalanceDest": 0,
        "newbalanceDest": 250000,
        "isFlaggedFraud": 1
    }

    result = predict_fraud(sample_transaction)
    print(result)