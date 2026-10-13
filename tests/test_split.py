import pandas as pd
import pytest

from fraudshield.data import split_summary, time_split
from fraudshield.synth import generate


@pytest.fixture(scope="module")
def df():
    return generate(n_cards=30, n_days=40, fraud_rate=0.02, seed=7)


def test_no_time_overlap(df):
    train, valid, test = time_split(df)
    assert train["event_time"].max() < valid["event_time"].min()
    assert valid["event_time"].max() < test["event_time"].min()


def test_split_on_day_boundaries(df):
    train, valid, test = time_split(df)
    # 40 days -> 28 / 6 / 6
    assert [s["event_time"].dt.normalize().nunique() for s in (train, valid, test)] == [28, 6, 6]
    assert train["event_time"].dt.normalize().max() < valid["event_time"].dt.normalize().min()


def test_partition_keeps_every_row_in_order(df):
    parts = pd.concat(time_split(df), ignore_index=True)
    assert parts.equals(df)  # nothing lost, nothing duplicated, order (event_time, tx_id) unchanged
    for card, rows in parts.groupby("card_id"):
        assert rows["event_time"].is_monotonic_increasing, card


def test_split_summary_reports_fraud_rate(df):
    summary = split_summary(dict(zip(("train", "valid", "test"), time_split(df), strict=True)))
    assert list(summary.index) == ["train", "valid", "test"]
    assert summary["rows"].sum() == len(df)
    assert all(0 < r < 0.1 for r in summary["fraud_rate"])


def test_too_few_days_rejected():
    with pytest.raises(ValueError, match="too few"):
        time_split(generate(n_cards=5, n_days=2, seed=0))
