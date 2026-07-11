from pathlib import Path
from datetime import datetime
import json
import joblib

import mlflow
import mlflow.sklearn
import mlflow.xgboost

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score
)
from sklearn.ensemble import RandomForestClassifier

from xgboost import XGBClassifier

from data_preprocessing import load_data, preprocess_data
from feature_engineering import add_features


# -------------------------------
# Paths
# -------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = BASE_DIR / "data" / "raw" / "paysim.csv"

MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "fraud_model.pkl"
ENCODER_PATH = MODEL_DIR / "label_encoder.pkl"
MODEL_METADATA_PATH = MODEL_DIR / "model_metadata.json"

REPORT_DIR = BASE_DIR / "reports"
RETRAINING_REPORT_PATH = REPORT_DIR / "retraining_report.json"


# -------------------------------
# MLflow Config
# -------------------------------

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("airflow_fraud_model_retraining")


# -------------------------------
# Helper Functions
# -------------------------------

def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "roc_auc": roc_auc_score(y_test, y_prob),
        "pr_auc": average_precision_score(y_test, y_prob),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1_score": f1_score(y_test, y_pred, zero_division=0),
    }

    return metrics, y_pred


def selection_score(metrics):
    """
    Fraud model custom selection score.

    PR-AUC is important for imbalanced fraud data.
    Recall is important because missing fraud cases is risky.

    Final Score = 70% PR-AUC + 30% Recall
    """
    return (0.7 * metrics["pr_auc"]) + (0.3 * metrics["recall"])


def train_and_log_model(model_name, model, params, X_train, X_test, y_train, y_test):
    with mlflow.start_run(run_name=model_name):
        mlflow.log_param("model_name", model_name)

        for key, value in params.items():
            mlflow.log_param(key, value)

        model.fit(X_train, y_train)

        metrics, y_pred = evaluate_model(model, X_test, y_test)

        final_score = selection_score(metrics)

        for key, value in metrics.items():
            mlflow.log_metric(key, value)

        mlflow.log_metric("selection_score", final_score)

        print("\n" + "=" * 80)
        print(f"MODEL: {model_name}")
        print("=" * 80)
        print(classification_report(y_test, y_pred))
        print("ROC-AUC:", metrics["roc_auc"])
        print("PR-AUC:", metrics["pr_auc"])
        print("Precision:", metrics["precision"])
        print("Recall:", metrics["recall"])
        print("F1 Score:", metrics["f1_score"])
        print("Selection Score:", final_score)

        if model_name == "xgboost":
            mlflow.xgboost.log_model(
                xgb_model=model,
                name=model_name
            )
        else:
            mlflow.sklearn.log_model(
                sk_model=model,
                name=model_name
            )

        return model, metrics


# -------------------------------
# Main Retraining Pipeline
# -------------------------------

def main():
    print("\nStarting fraud model retraining pipeline...")

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {DATA_PATH}. "
            "Please place your dataset as data/raw/paysim.csv"
        )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading dataset from:", DATA_PATH)

    df = load_data(DATA_PATH)

    print("Original dataset shape:", df.shape)

    if len(df) > 100000:
        df = df.sample(n=100000, random_state=42)

    print("Training dataset shape:", df.shape)

    df, label_encoder = preprocess_data(df)
    df = add_features(df)

    if "isFraud" not in df.columns:
        raise ValueError("Target column 'isFraud' not found in dataset.")

    X = df.drop("isFraud", axis=1)
    y = df["isFraud"]

    if y.nunique() < 2:
        raise ValueError(
            "Training data has only one class. "
            "Fraud and non-fraud both classes are required."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    fraud_count = int(y_train.sum())
    non_fraud_count = int(len(y_train) - fraud_count)

    if fraud_count == 0:
        scale_pos_weight = 1
    else:
        scale_pos_weight = non_fraud_count / fraud_count

    print("Fraud count in training:", fraud_count)
    print("Non-fraud count in training:", non_fraud_count)
    print("scale_pos_weight:", scale_pos_weight)

    trained_models = []

    # -------------------------------
    # Random Forest
    # -------------------------------

    rf_params = {
        "n_estimators": 100,
        "max_depth": 10,
        "class_weight": "balanced",
        "random_state": 42
    }

    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    trained_rf, rf_metrics = train_and_log_model(
        model_name="random_forest",
        model=rf_model,
        params=rf_params,
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test
    )

    trained_models.append(("random_forest", trained_rf, rf_metrics))

    # -------------------------------
    # XGBoost
    # -------------------------------

    xgb_params = {
        "n_estimators": 150,
        "max_depth": 5,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "scale_pos_weight": scale_pos_weight,
        "random_state": 42
    }

    xgb_model = XGBClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric="logloss",
        n_jobs=-1
    )

    trained_xgb, xgb_metrics = train_and_log_model(
        model_name="xgboost",
        model=xgb_model,
        params=xgb_params,
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test
    )

    trained_models.append(("xgboost", trained_xgb, xgb_metrics))

    # -------------------------------
    # Select Best Model
    # -------------------------------

    best_model_name, best_model, best_metrics = max(
        trained_models,
        key=lambda item: selection_score(item[2])
    )

    best_score = selection_score(best_metrics)

    print("\n" + "#" * 80)
    print("BEST MODEL SELECTED:", best_model_name)
    print("BEST PR-AUC:", best_metrics["pr_auc"])
    print("BEST RECALL:", best_metrics["recall"])
    print("BEST SELECTION SCORE:", best_score)
    print("#" * 80)

    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(label_encoder, ENCODER_PATH)

    metadata = {
        "retrained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_path": str(DATA_PATH),
        "training_rows": int(len(df)),
        "features": list(X.columns),
        "target": "isFraud",
        "best_model_name": best_model_name,
        "best_metrics": best_metrics,
        "best_selection_score": best_score,
        "model_path": str(MODEL_PATH),
        "encoder_path": str(ENCODER_PATH)
    }

    with open(MODEL_METADATA_PATH, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)

    with open(RETRAINING_REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)

    print("\nRetraining completed successfully.")
    print("Best model saved at:", MODEL_PATH)
    print("Label encoder saved at:", ENCODER_PATH)
    print("Model metadata saved at:", MODEL_METADATA_PATH)
    print("Retraining report saved at:", RETRAINING_REPORT_PATH)


if __name__ == "__main__":
    main()