def add_features(df):
    df = df.copy()

    df["balance_diff_orig"] = df["oldbalanceOrg"] - df["newbalanceOrig"]
    df["balance_diff_dest"] = df["newbalanceDest"] - df["oldbalanceDest"]

    df["amount_to_oldbalance_ratio"] = df["amount"] / (df["oldbalanceOrg"] + 1)

    df["is_zero_balance_after_txn"] = (df["newbalanceOrig"] == 0).astype(int)

    return df