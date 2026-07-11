from pathlib import Path
import joblib
import pandas as pd
import numpy as np

from feature_engineering import add_features


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "models" / "fraud_model.pkl"
ENCODER_PATH = BASE_DIR / "models" / "label_encoder.pkl"

model = joblib.load(MODEL_PATH)
label_encoder = joblib.load(ENCODER_PATH)


def prepare_transaction_features(transaction):
    df = pd.DataFrame([transaction])

    txn_type = str(df.loc[0, "type"]).upper()
    df.loc[0, "type"] = txn_type

    if txn_type not in label_encoder.classes_:
        raise ValueError(
            f"Invalid transaction type: {txn_type}. "
            f"Allowed types are: {list(label_encoder.classes_)}"
        )

    df["type"] = label_encoder.transform(df["type"])

    df = add_features(df)

    return df


def explain_transaction(transaction, top_n=5):
    """
    Explains a single transaction prediction.

    First tries SHAP.
    If SHAP fails, falls back to model feature importance.
    """

    df = prepare_transaction_features(transaction)

    try:
        import shap

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(df)

        # Different models return SHAP values in different formats
        if isinstance(shap_values, list):
            values = shap_values[1][0]
        else:
            values = shap_values[0]

        explanations = []

        for feature, value, shap_value in zip(df.columns, df.iloc[0], values):
            explanations.append({
                "feature": feature,
                "feature_value": float(value),
                "impact_score": float(shap_value)
            })

        explanations = sorted(
            explanations,
            key=lambda x: abs(x["impact_score"]),
            reverse=True
        )

        return {
            "explanation_method": "SHAP",
            "top_features": explanations[:top_n]
        }

    except Exception as e:
        explanations = []

        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_

            for feature, value, importance in zip(df.columns, df.iloc[0], importances):
                explanations.append({
                    "feature": feature,
                    "feature_value": float(value),
                    "impact_score": float(importance)
                })

            explanations = sorted(
                explanations,
                key=lambda x: x["impact_score"],
                reverse=True
            )

            return {
                "explanation_method": "Feature Importance Fallback",
                "top_features": explanations[:top_n],
                "shap_error": str(e)
            }

        return {
            "explanation_method": "Explanation Failed",
            "top_features": [],
            "error": str(e)
        }


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

    explanation = explain_transaction(sample_transaction)
    print(explanation)