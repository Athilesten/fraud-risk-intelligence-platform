from rules_engine import evaluate_rules


def test_high_risk_transaction_triggers_rules():
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

    result = evaluate_rules(transaction)

    assert result["rule_risk_score"] >= 70
    assert result["rule_risk_level"] == "HIGH"
    assert len(result["triggered_rules"]) > 0


def test_low_risk_transaction_has_low_score():
    transaction = {
        "step": 1,
        "type": "PAYMENT",
        "amount": 500,
        "oldbalanceOrg": 5000,
        "newbalanceOrig": 4500,
        "oldbalanceDest": 0,
        "newbalanceDest": 0,
        "isFlaggedFraud": 0
    }

    result = evaluate_rules(transaction)

    assert result["rule_risk_score"] < 40
    assert result["rule_risk_level"] == "LOW"