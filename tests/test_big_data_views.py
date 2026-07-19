from pathlib import Path

import src.big_data_views as big_data_views


def test_datalake_summary_returns_zero_when_tables_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        big_data_views,
        "DELTA_TABLE_CANDIDATES",
        {
            "bronze": [tmp_path / "bronze"],
            "silver": [tmp_path / "silver"],
            "gold": [tmp_path / "gold"],
            "scored_gold": [tmp_path / "scored_gold"],
        },
    )
    monkeypatch.setattr(big_data_views, "KAFKA_SCORED_LOG_PATH", tmp_path / "missing.csv")

    summary = big_data_views.get_datalake_summary()

    assert summary["available"] is False
    assert summary["bronze_count"] == 0
    assert summary["silver_count"] == 0


def test_read_recent_csv_returns_latest_rows_first(tmp_path):
    csv_path = tmp_path / "scored.csv"
    csv_path.write_text("event_id,type\n1,PAYMENT\n2,TRANSFER\n", encoding="utf-8")

    rows = big_data_views.read_recent_csv(Path(csv_path), limit=2)

    assert rows[0]["event_id"] == "2"
    assert rows[1]["event_id"] == "1"
