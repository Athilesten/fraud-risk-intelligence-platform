from pathlib import Path
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, average_precision_score
from sklearn.ensemble import RandomForestClassifier

from data_preprocessing import load_data, preprocess_data
from feature_engineering import add_features


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "raw" / "paysim.csv"

print("Looking for dataset at:", DATA_PATH)

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"\nDataset not found at: {DATA_PATH}\n"
        "Please put your PaySim CSV file inside data/raw/ and rename it to paysim.csv\n"
    )

df = load_data(DATA_PATH)

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

model.fit(X_train, y_train)

y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

print("Classification Report:")
print(classification_report(y_test, y_pred))

print("ROC-AUC:", roc_auc_score(y_test, y_prob))
print("PR-AUC:", average_precision_score(y_test, y_prob))

model_path = BASE_DIR / "models" / "fraud_model.pkl"
encoder_path = BASE_DIR / "models" / "label_encoder.pkl"

joblib.dump(model, model_path)
joblib.dump(label_encoder, encoder_path)

print("Model saved successfully.")
print("Saved model at:", model_path)