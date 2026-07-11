import pandas as pd

from feature_engineering import add_features


def test_add_features_creates_expected_columns():
    df = pd.DataFrame([
        {
            "step": 1,
            "type": 1,
            "amount": 1000,
            "oldbalanceOrg": 5000,
            "newbalanceOrig": 4000,
            "oldbalanceDest": 1000,
            "newbalanceDest": 2000,
            "isFlaggedFraud": 0
        }
    ])

    result = add_features(df)

    assert "balance_diff_orig" in result.columns
    assert "balance_diff_dest" in result.columns
    assert "amount_to_oldbalance_ratio" in result.columns
    assert "is_zero_balance_after_txn" in result.columns


def test_add_features_values_are_correct():
    df = pd.DataFrame([
        {
            "step": 1,
            "type": 1,
            "amount": 1000,
            "oldbalanceOrg": 5000,
            "newbalanceOrig": 4000,
            "oldbalanceDest": 1000,
            "newbalanceDest": 2000,
            "isFlaggedFraud": 0
        }
    ])

    result = add_features(df)

    assert result.loc[0, "balance_diff_orig"] == 1000
    assert result.loc[0, "balance_diff_dest"] == 1000
    assert result.loc[0, "is_zero_balance_after_txn"] == 0