"""Small synthetic transaction generator in the canonical schema, for tests and demos.

Each card has a home location, a few habitual categories, a spending level and a daily rhythm.
Fraud is injected as episodes on random cards, using any of these patterns:
  burst           5-10 transactions within 10 minutes
  far_away        1-3 transactions at a merchant 1,300+ km from home
  unusual_amount  one transaction at 15-40x the card's usual amount for that category
  new_category    1-3 transactions in a category the card never uses
Rows are produced in Sparkov's raw columns and passed through `to_canonical`, so the schema is identical
to the real data.
"""

import numpy as np
import pandas as pd

from fraudshield.data import to_canonical

PATTERNS = ("burst", "far_away", "unusual_amount", "new_category")

# Typical amount (USD) per category, roughly in line with Sparkov
CATEGORY_AMOUNT = {
    "grocery_pos": 60, "grocery_net": 50, "gas_transport": 60, "shopping_pos": 40, "shopping_net": 50,
    "food_dining": 30, "entertainment": 40, "health_fitness": 35, "personal_care": 25, "kids_pets": 40,
    "home": 45, "misc_pos": 30, "misc_net": 40, "travel": 80,
}  # fmt: skip
CATEGORIES = list(CATEGORY_AMOUNT)
STATES = ["NY", "CA", "TX", "PA", "OH", "IL", "MI", "FL", "AL", "MO"]
JOBS = ["Nurse", "Engineer", "Teacher", "Chef", "Accountant", "Designer", "Driver", "Lawyer"]
# Daily rhythm: quiet at night, busiest afternoon/evening
HOUR_WEIGHTS = np.array([1, 1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 6, 8, 8, 7, 7, 8, 9, 9, 8, 6, 4, 2, 1], float)
HOUR_P = HOUR_WEIGHTS / HOUR_WEIGHTS.sum()


def generate(
    n_cards: int = 50,
    n_days: int = 30,
    fraud_rate: float = 0.01,
    patterns: tuple[str, ...] = PATTERNS,
    seed: int = 0,
    start: str = "2019-01-01",
) -> pd.DataFrame:
    """Return canonical transactions sorted by (event_time, tx_id). Deterministic for a given seed.

    Fraud episodes are added until at least `fraud_rate` of all rows are fraud (none if `patterns` is empty).
    """
    unknown = set(patterns) - set(PATTERNS)
    if unknown:
        raise ValueError(f"unknown patterns: {unknown}")
    rng = np.random.default_rng(seed)
    t0 = pd.Timestamp(start)
    cards = [_card(rng, i, t0) for i in range(n_cards)]
    rows = []

    for c in cards:
        n = rng.poisson(c["tx_per_day"] * n_days)
        secs = (
            rng.integers(0, n_days, n) * 86_400
            + rng.choice(24, n, p=HOUR_P) * 3_600
            + rng.integers(0, 3_600, n)
        )
        for s, cat in zip(secs, rng.choice(c["categories"], n, p=c["category_p"]), strict=True):
            rows.append(_tx(rng, c, t0, int(s), cat))

    n_legit = len(rows)
    while patterns and len(rows) - n_legit < fraud_rate * len(rows):
        c = cards[rng.integers(n_cards)]
        rows += _episode(rng, c, t0, rng.choice(patterns), int(rng.integers(0, n_days * 86_400 - 3_600)))

    raw = pd.DataFrame(rows)
    raw["trans_num"] = [f"syn{i:07d}" for i in range(len(raw))]
    return to_canonical(raw)


def _card(rng: np.random.Generator, i: int, t0: pd.Timestamp) -> dict:
    categories = rng.choice(CATEGORIES, size=4, replace=False)
    return {
        "cc_num": 4_000_000_000_000_000 + i,
        "lat": rng.uniform(30, 47),
        "long": rng.uniform(-120, -75),
        "city_pop": int(10 ** rng.uniform(3, 6.5)),
        "gender": rng.choice(["F", "M"]),
        "job": rng.choice(JOBS),
        "state": rng.choice(STATES),
        "zip": int(rng.integers(10_000, 99_999)),
        "dob": (t0 - pd.Timedelta(days=int(rng.uniform(18, 85) * 365.25))).date().isoformat(),
        "tx_per_day": rng.uniform(1, 5),
        "spend": rng.uniform(0.7, 1.5),
        "categories": categories,
        "category_p": rng.dirichlet(np.ones(len(categories))),
    }


def _tx(rng, c, t0, secs, category, fraud=0, amount=None, merch_lat=None, merch_long=None) -> dict:
    if amount is None:
        amount = CATEGORY_AMOUNT[category] * c["spend"] * rng.lognormal(0, 0.5)
    return {
        "trans_date_trans_time": t0 + pd.Timedelta(seconds=secs),
        "cc_num": c["cc_num"],
        "merchant": f"m_{category}_{rng.integers(20)}",
        "category": category,
        "amt": round(float(amount), 2),
        "lat": c["lat"],
        "long": c["long"],
        "merch_lat": c["lat"] + rng.uniform(-0.5, 0.5) if merch_lat is None else merch_lat,
        "merch_long": c["long"] + rng.uniform(-0.5, 0.5) if merch_long is None else merch_long,
        "city_pop": c["city_pop"],
        "gender": c["gender"],
        "job": c["job"],
        "state": c["state"],
        "zip": c["zip"],
        "dob": c["dob"],
        "is_fraud": fraud,
    }


def _episode(rng, c, t0, pattern: str, start: int) -> list[dict]:
    habitual = list(c["categories"])
    if pattern == "burst":
        offsets = np.sort(rng.integers(0, 600, rng.integers(5, 11)))
        return [_tx(rng, c, t0, start + int(o), rng.choice(habitual), fraud=1) for o in offsets]
    if pattern == "far_away":
        # 12-20 degrees of latitude away is at least ~1,300 km
        lat = c["lat"] + rng.choice([-1, 1]) * rng.uniform(12, 20)
        lon = c["long"] + rng.uniform(-5, 5)
        offsets = np.sort(rng.integers(0, 3_600, rng.integers(1, 4)))
        return [_tx(rng, c, t0, start + int(o), rng.choice(habitual), 1, None, lat, lon) for o in offsets]
    if pattern == "unusual_amount":
        cat = rng.choice(habitual, p=c["category_p"])  # a category the card actually uses
        amount = CATEGORY_AMOUNT[cat] * c["spend"] * rng.uniform(15, 40)
        return [_tx(rng, c, t0, start, cat, fraud=1, amount=amount)]
    # new_category
    cat = rng.choice([k for k in CATEGORIES if k not in habitual])
    offsets = np.sort(rng.integers(0, 3_600, rng.integers(1, 4)))
    return [_tx(rng, c, t0, start + int(o), cat, fraud=1) for o in offsets]
