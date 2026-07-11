from pathlib import Path
import joblib
import mlflow
import mlflow.sklearn
import pandas as pd

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

from data_preprocessing import load_data, preprocess_data
from feature_engineering import add_features


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = BASE_DIR / "data" / "raw" / "paysim.csv"
MODEL_PATH = BASE_DIR / "models" / "fraud_model.pkl"
ENCODER_PATH = BASE_DIR / "models" / "label_encoder.pkl"

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("fraud_detection_experiment")

def train_model():
    print("Loading dataset from:", DATA_PATH)

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {DATA_PATH}. "
            "Please place your PaySim CSV as data/raw/paysim.csv"
        )

    df = load_data(DATA_PATH)

    print("Original dataset shape:", df.shape)

    # Optional sampling for large dataset
    # If your laptop is slow, keep 100000.
    # If you want full training later, comment these 2 lines.
    if len(df) > 100000:
        df = df.sample(n=100000, random_state=42)

    print("Training dataset shape:", df.shape)

    df, label_encoder = preprocess_data(df)
    df = add_features(df)

    X = df.drop("isFraud", axis=1)
    y = df["isFraud"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )

    with mlflow.start_run(run_name="random_forest_baseline"):

        mlflow.log_param("model_type", "RandomForestClassifier")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 10)
        mlflow.log_param("class_weight", "balanced")
        mlflow.log_param("test_size", 0.2)
        mlflow.log_param("training_rows", len(X_train))
        mlflow.log_param("testing_rows", len(X_test))

        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        roc_auc = roc_auc_score(y_test, y_prob)
        pr_auc = average_precision_score(y_test, y_prob)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        mlflow.log_metric("roc_auc", roc_auc)
        mlflow.log_metric("pr_auc", pr_auc)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("f1_score", f1)

        print("Classification Report:")
        print(classification_report(y_test, y_pred))

        print("ROC-AUC:", roc_auc)
        print("PR-AUC:", pr_auc)
        print("Precision:", precision)
        print("Recall:", recall)
        print("F1 Score:", f1)

        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(model, MODEL_PATH)
        joblib.dump(label_encoder, ENCODER_PATH)

        mlflow.sklearn.log_model(model, artifact_path="fraud_model")
        mlflow.log_artifact(str(MODEL_PATH))
        mlflow.log_artifact(str(ENCODER_PATH))

        print("Model saved at:", MODEL_PATH)
        print("Label encoder saved at:", ENCODER_PATH)
        print("MLflow run completed successfully.")


if __name__ == "__main__":
    train_model()