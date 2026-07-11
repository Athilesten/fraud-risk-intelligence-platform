from pathlib import Path
import pytest


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "fraud_model.pkl"
ENCODER_PATH = BASE_DIR / "models" / "label_encoder.pkl"

if not MODEL_PATH.exists() or not ENCODER_PATH.exists():
    pytest.skip(
        "Model artifacts not found. Skipping prediction tests.",
        allow_module_level=True
    )

from predict import predict_fraud


def test_predict_fraud_returns_expected_keys():
    transaction = {
        "step": 1,
        "type": "TRANSFER",
        "amount": 250000,
        "oldbalanceOrg": 250000,
        "newbalanceOrig": 0,
        "oldbalanceDest": 0,
        "newbalanceDest": 250000,
        "isFlaggedFraud": 1
    }

    result = predict_fraud(transaction)

    assert "fraud_probability" in result
    assert "risk_level" in result
    assert "alert" in result
    assert "rule_risk_score" in result
    assert "rule_risk_level" in result
    assert "triggered_rules" in result
    assert "final_decision" in result


def test_predict_fraud_invalid_transaction_type_raises_error():
    transaction = {
        "step": 1,
        "type": "INVALID_TYPE",
        "amount": 1000,
        "oldbalanceOrg": 5000,
        "newbalanceOrig": 4000,
        "oldbalanceDest": 0,
        "newbalanceDest": 1000,
        "isFlaggedFraud": 0
    }

    with pytest.raises(ValueError):
        predict_fraud(transaction)