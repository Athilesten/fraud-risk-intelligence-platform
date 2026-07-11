def evaluate_rules(transaction):
    """
    Rule-based fraud detection engine.

    This does not replace ML model.
    It supports the ML model by adding explainable fraud rules.
    """

    triggered_rules = []
    rule_risk_score = 0

    txn_type = str(transaction.get("type", "")).upper()
    amount = float(transaction.get("amount", 0))
    oldbalance_org = float(transaction.get("oldbalanceOrg", 0))
    newbalance_orig = float(transaction.get("newbalanceOrig", 0))
    oldbalance_dest = float(transaction.get("oldbalanceDest", 0))
    newbalance_dest = float(transaction.get("newbalanceDest", 0))
    is_flagged_fraud = int(transaction.get("isFlaggedFraud", 0))

    # Rule 1: Very high amount
    if amount >= 200000:
        triggered_rules.append("High value transaction amount >= 200000")
        rule_risk_score += 25

    # Rule 2: Sender balance becomes zero
    if oldbalance_org > 0 and newbalance_orig == 0 and txn_type in ["TRANSFER", "CASH_OUT"]:
        triggered_rules.append("Sender balance became zero after transaction")
        rule_risk_score += 25

    # Rule 3: Suspicious transaction type
    if txn_type in ["TRANSFER", "CASH_OUT"]:
        triggered_rules.append("Risky transaction type: TRANSFER/CASH_OUT")
        rule_risk_score += 15

    # Rule 4: System already flagged fraud
    if is_flagged_fraud == 1:
        triggered_rules.append("Transaction already flagged by system rule")
        rule_risk_score += 30

    # Rule 5: Sender balance mismatch
    expected_newbalance_orig = oldbalance_org - amount

    if txn_type != "CASH_IN" and oldbalance_org >= amount:
        balance_gap = abs(expected_newbalance_orig - newbalance_orig)

        if balance_gap > 1:
            triggered_rules.append("Sender balance movement mismatch")
            rule_risk_score += 15

    # Rule 6: Receiver balance mismatch for transfer/cash-out
    if txn_type in ["TRANSFER", "CASH_OUT"]:
        expected_newbalance_dest = oldbalance_dest + amount
        receiver_gap = abs(expected_newbalance_dest - newbalance_dest)

        if receiver_gap > 1:
            triggered_rules.append("Receiver balance movement mismatch")
            rule_risk_score += 15

    # Keep score max 100
    rule_risk_score = min(rule_risk_score, 100)

    if rule_risk_score >= 70:
        rule_risk_level = "HIGH"
    elif rule_risk_score >= 40:
        rule_risk_level = "MEDIUM"
    else:
        rule_risk_level = "LOW"

    return {
        "rule_risk_score": rule_risk_score,
        "rule_risk_level": rule_risk_level,
        "triggered_rules": triggered_rules
    }