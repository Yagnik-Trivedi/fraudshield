import numpy as np
import pytest

from fraudshield.schema import COLUMNS, Transaction
from fraudshield.synth import generate


def km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def test_shape_schema_and_order():
    df = generate(n_cards=20, n_days=10, seed=1)
    assert list(df.columns) == COLUMNS
    assert df["card_id"].nunique() == 20
    assert df["event_time"].min() >= np.datetime64("2019-01-01")
    assert df["event_time"].max() < np.datetime64("2019-01-11")
    assert df["tx_id"].is_unique
    assert df[["event_time", "tx_id"]].equals(
        df[["event_time", "tx_id"]].sort_values(["event_time", "tx_id"])
    )
    Transaction.model_validate(df.iloc[0].to_dict())


def test_deterministic():
    assert generate(seed=3).equals(generate(seed=3))
    assert not generate(seed=3).equals(generate(seed=4))


def test_fraud_rate():
    df = generate(n_cards=50, n_days=30, fraud_rate=0.02, seed=0)
    assert 0.02 <= df["is_fraud"].mean() < 0.025  # overshoots by at most one episode
    assert generate(patterns=(), seed=0)["is_fraud"].sum() == 0


def test_unknown_pattern_rejected():
    with pytest.raises(ValueError):
        generate(patterns=("teleport",))


def test_burst():
    fraud = generate(patterns=("burst",), seed=0).query("is_fraud == 1")
    # some card has 5 fraud transactions within 10 minutes
    gaps = fraud.groupby("card_id")["event_time"].transform(lambda t: t.diff(4).dt.total_seconds())
    assert (gaps <= 600).any()


def test_far_away():
    df = generate(patterns=("far_away",), seed=0)
    dist = km(df["lat"], df["lon"], df["merch_lat"], df["merch_lon"])
    assert (dist[df["is_fraud"] == 1] > 1_000).all()
    assert (dist[df["is_fraud"] == 0] < 100).all()


def test_unusual_amount():
    df = generate(patterns=("unusual_amount",), seed=0)
    usual = df[df["is_fraud"] == 0].groupby(["card_id", "category"], observed=True)["amount"].median()
    fraud = df[df["is_fraud"] == 1].join(usual.rename("usual"), on=["card_id", "category"]).dropna()
    # generator uses 15-40x; a per-category median can rest on few legit rows, so test 5x
    assert len(fraud) > 10
    assert (fraud["amount"] > 5 * fraud["usual"]).all()


def test_new_category():
    df = generate(patterns=("new_category",), seed=0)
    legit = df[df["is_fraud"] == 0].astype({"category": str})
    habitual = legit.groupby("card_id")["category"].agg(set)
    fraud = df[df["is_fraud"] == 1]
    assert all(
        cat not in habitual[card] for card, cat in zip(fraud["card_id"], fraud["category"], strict=True)
    )
