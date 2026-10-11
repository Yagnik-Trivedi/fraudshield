"""Load the raw Sparkov CSVs into one canonical, time-sorted Parquet file.

uv run python -m fraudshield.data              # data/processed/transactions.parquet
uv run python -m fraudshield.data --sample 0.1 # + sample_10pct.parquet (10% of cards, all their rows)
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from fraudshield.config import get_settings
from fraudshield.schema import COLUMNS, SPARKOV_COLUMNS

RAW_FILES = ("fraudTrain.csv", "fraudTest.csv")
CATEGORICAL = ("category", "gender", "state")


def to_canonical(raw: pd.DataFrame) -> pd.DataFrame:
    """Rename, type and sort raw Sparkov rows into the canonical schema."""
    df = raw[list(SPARKOV_COLUMNS)].rename(columns=SPARKOV_COLUMNS)
    df["event_time"] = pd.to_datetime(df["event_time"])
    df["dob"] = pd.to_datetime(df["dob"])
    df["age"] = ((df["event_time"] - df["dob"]).dt.days // 365.25).astype("int16")
    df["tx_id"] = df["tx_id"].astype(str)
    df["card_id"] = df["card_id"].astype("int64")
    df["is_fraud"] = df["is_fraud"].astype("int8")
    for col in CATEGORICAL:
        df[col] = df[col].astype("category")
    # (event_time, tx_id) is the processing order everywhere: offline features, the stream, parity tests.
    return df[COLUMNS].sort_values(["event_time", "tx_id"], ignore_index=True)


def load_raw(raw_dir: Path) -> pd.DataFrame:
    frames = [pd.read_csv(raw_dir / name) for name in RAW_FILES]
    df = to_canonical(pd.concat(frames, ignore_index=True))
    if df["tx_id"].duplicated().any():
        raise ValueError("duplicate trans_num across raw files")
    return df


def card_sample(df: pd.DataFrame, frac: float, seed: int) -> pd.DataFrame:
    """Keep every transaction of a random `frac` of cards, so per-card velocity features stay correct."""
    cards = df["card_id"].unique()
    rng = np.random.default_rng(seed)
    keep = rng.choice(cards, size=max(1, round(len(cards) * frac)), replace=False)
    return df[df["card_id"].isin(keep)].reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--sample", type=float, help="also write a card-level sample of this fraction")
    args = parser.parse_args()

    s = get_settings()
    out = Path(s.processed_dir)
    out.mkdir(parents=True, exist_ok=True)

    df = load_raw(Path(s.raw_dir))
    df.to_parquet(out / "transactions.parquet", index=False)
    print(
        f"transactions.parquet: {len(df):,} rows, {df['card_id'].nunique():,} cards, "
        f"fraud rate {df['is_fraud'].mean():.4%}, {df['event_time'].min()} .. {df['event_time'].max()}"
    )

    if args.sample:
        sample = card_sample(df, args.sample, s.random_seed)
        name = f"sample_{round(args.sample * 100)}pct.parquet"
        sample.to_parquet(out / name, index=False)
        print(f"{name}: {len(sample):,} rows, {sample['card_id'].nunique():,} cards")


if __name__ == "__main__":
    main()
