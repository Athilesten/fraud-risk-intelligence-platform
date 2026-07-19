import pandas as pd

from drift_monitoring import build_drift_report, population_stability_index


def test_population_stability_index_detects_shift():
    baseline = [100, 110, 120, 130, 140, 150, 160, 170, 180, 190]
    current = [1000, 1100, 1200, 1300, 1400]

    psi = population_stability_index(baseline, current, buckets=5)

    assert psi is not None
    assert psi > 0.25


def test_build_drift_report_flags_high_numeric_drift():
    baseline_df = pd.DataFrame({
        "amount": [100, 120, 130, 140, 150, 160, 170, 180],
        "type": ["PAYMENT", "PAYMENT", "TRANSFER", "CASH_OUT"] * 2
    })
    current_df = pd.DataFrame({
        "amount": [2000, 2200, 2300, 2400],
        "type": ["TRANSFER", "TRANSFER", "CASH_OUT", "CASH_OUT"]
    })

    report = build_drift_report(baseline_df, current_df)

    assert report["requires_review"] is True
    assert "amount" in report["high_drift_features"]
    assert "type" in report["categorical_shift"]
