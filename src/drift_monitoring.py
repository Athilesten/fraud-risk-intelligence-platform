import numpy as np
import pandas as pd


NUMERIC_FEATURES = [
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
    "balance_diff_orig",
    "balance_diff_dest",
    "amount_to_oldbalance_ratio"
]

CATEGORICAL_FEATURES = ["type", "final_decision", "risk_level"]


def population_stability_index(expected, actual, buckets=10):
    expected = pd.Series(expected).dropna().astype(float)
    actual = pd.Series(actual).dropna().astype(float)

    if expected.empty or actual.empty:
        return None

    quantiles = np.linspace(0, 1, buckets + 1)
    breakpoints = np.unique(np.quantile(expected, quantiles))

    if len(breakpoints) < 2:
        return 0.0

    expected_counts = np.histogram(expected, bins=breakpoints)[0]
    actual_counts = np.histogram(actual, bins=breakpoints)[0]

    expected_pct = np.clip(expected_counts / max(expected_counts.sum(), 1), 0.0001, None)
    actual_pct = np.clip(actual_counts / max(actual_counts.sum(), 1), 0.0001, None)

    return float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))


def categorical_distribution_shift(expected, actual):
    expected_counts = pd.Series(expected).fillna("UNKNOWN").astype(str).value_counts(normalize=True)
    actual_counts = pd.Series(actual).fillna("UNKNOWN").astype(str).value_counts(normalize=True)

    categories = sorted(set(expected_counts.index).union(actual_counts.index))

    return {
        category: {
            "baseline_pct": float(expected_counts.get(category, 0.0)),
            "current_pct": float(actual_counts.get(category, 0.0)),
            "absolute_change": float(abs(actual_counts.get(category, 0.0) - expected_counts.get(category, 0.0)))
        }
        for category in categories
    }


def drift_severity(psi):
    if psi is None:
        return "UNKNOWN"

    if psi >= 0.25:
        return "HIGH"

    if psi >= 0.10:
        return "MEDIUM"

    return "LOW"


def build_drift_report(baseline_df, current_df):
    numeric_results = {}

    for feature in NUMERIC_FEATURES:
        if feature in baseline_df.columns and feature in current_df.columns:
            psi = population_stability_index(baseline_df[feature], current_df[feature])
            numeric_results[feature] = {
                "psi": psi,
                "severity": drift_severity(psi)
            }

    categorical_results = {}

    for feature in CATEGORICAL_FEATURES:
        if feature in baseline_df.columns and feature in current_df.columns:
            categorical_results[feature] = categorical_distribution_shift(
                baseline_df[feature],
                current_df[feature]
            )

    high_drift_features = [
        feature
        for feature, result in numeric_results.items()
        if result["severity"] == "HIGH"
    ]

    return {
        "numeric_drift": numeric_results,
        "categorical_shift": categorical_results,
        "high_drift_features": high_drift_features,
        "requires_review": bool(high_drift_features)
    }
