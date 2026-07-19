import pytest

from streaming.schema_validator import (
    SchemaValidationError,
    validate_raw_event,
    validate_scored_event,
)


def test_validate_raw_event_accepts_valid_payload():
    event = {
        "event_id": "evt-1",
        "event_time": "2026-07-18T00:00:00Z",
        "source_dataset": "paysim",
        "step": 1,
        "type": "TRANSFER",
        "amount": 250000.0,
        "oldbalanceOrg": 250000.0,
        "newbalanceOrig": 0.0,
        "oldbalanceDest": 0.0,
        "newbalanceDest": 250000.0,
        "isFlaggedFraud": 1,
    }

    assert validate_raw_event(event) is True


def test_validate_raw_event_rejects_missing_required_field():
    event = {
        "event_id": "evt-1",
        "event_time": "2026-07-18T00:00:00Z",
        "source_dataset": "paysim",
    }

    with pytest.raises(SchemaValidationError):
        validate_raw_event(event)


def test_validate_scored_event_accepts_valid_payload():
    event = {
        "event_id": "evt-1",
        "event_time": "2026-07-18T00:00:00Z",
        "source_dataset": "paysim",
        "type": "TRANSFER",
        "amount": 250000.0,
        "prediction": {
            "fraud_probability": 0.69,
            "risk_level": "MEDIUM",
            "rule_risk_score": 95,
            "rule_risk_level": "HIGH",
            "final_decision": "BLOCK / MANUAL REVIEW",
            "triggered_rules": ["High value transaction"],
        },
        "scored_at": "2026-07-18T00:00:01Z",
    }

    assert validate_scored_event(event) is True
