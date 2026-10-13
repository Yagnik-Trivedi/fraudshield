# Data

## Primary dataset: Sparkov simulated credit-card transactions
- Kaggle: `kartik2112/fraud-detection` (files `fraudTrain.csv`, `fraudTest.csv`)
- About 1.85M transactions, about 1,000 customers, Jan 2019 – Dec 2020, about 0.5% fraud
- Generated with the Sparkov Data Generation tool, so **synthetic**

### Download (Windows PowerShell)
```powershell
uv tool install kaggle
# Put kaggle.json (Kaggle → Settings → API → Create New Token) in $HOME\.kaggle\kaggle.json
kaggle datasets download -d kartik2112/fraud-detection -p data/raw --unzip
```
Alternatively download the zip from the Kaggle page in a browser and unzip it into `data/raw/`.

### Columns (verify against the files after download)
| Column | Use |
|---|---|
| `trans_date_trans_time` → `event_time` | event time. `unix_time` is offset from it in this dataset, so it is dropped |
| `cc_num` | card id → entity key for behavioural features |
| `merchant`, `category` | merchant id / category |
| `amt` | amount |
| `lat`, `long` | cardholder location |
| `merch_lat`, `merch_long` | merchant location → distance features |
| `city_pop`, `dob`, `gender`, `job`, `state`, `zip` | customer attributes (`dob` → age at transaction time) |
| `trans_num` | transaction id (idempotency key, tie-breaker) |
| `is_fraud` | label |
| `first`, `last`, `street` | **drop**: personal data, no legitimate signal |

### Splits
- Concatenate train + test files, sort by time, then split **by time**: train (first ~70% of days), validation (next ~15%), test (last ~15%).
- Assert `max(train.time) < min(valid.time)` and the same for valid/test in a test.
- Iterate on a 10% **card-level** sample (keep all transactions of the sampled cards) so velocity features stay correct.

### Leakage checklist
- [ ] No feature uses information from the same or later transactions of the card (windows are `[t − w, t)`)
- [ ] Target/category encodings are fit on train only
- [ ] No identity columns (`trans_num`, names) used as features
- [ ] Threshold chosen on validation, reported on test

## Secondary benchmark (Phase 6): IEEE-CIS Fraud Detection
590,540 card-not-present transactions, 394 features, ~3.5% fraud (Kaggle competition data; accept the competition rules to download). Offline only.

## Caveat to state in the README
Synthetic generators often fail to preserve real behavioural fraud patterns (see the 2026 benchmark
paper linked below), so results show the engineering approach, not real-world performance.

### Loaded (Oct 11)
`uv run python -m fraudshield.data --sample 0.1`: 1,852,394 rows, 999 cards, fraud rate 0.521%,
2019-01-01 → 2020-12-31. 10% card sample: 185,182 rows, 100 cards. About 15 s on the laptop.

### Time split (Oct 13, `data.time_split`, 70/15/15 of calendar days)
| Split | Rows | From | To | Fraud rate |
|---|---|---|---|---|
| train | 1,226,927 | 2019-01-01 | 2020-05-26 | 0.579% |
| valid | 301,468 | 2020-05-27 | 2020-09-12 | 0.468% |
| test | 323,999 | 2020-09-13 | 2020-12-31 | 0.350% |

The fraud rate falls over time, so the test set has fewer positives than train. PR-AUC depends on the base
rate, so test PR-AUC will look lower than validation PR-AUC even for the same model. Compare PR-AUC to the
split's base rate, and choose thresholds on validation.

## EDA findings
From `notebooks/01_eda.ipynb` (10% card sample: 185,182 rows, 100 cards, 968 fraud, base rate 0.523%).
These describe the Sparkov generator, not real fraud.

1. **Time of day is the strongest single signal.** 22:00–03:59 holds 83% of all fraud. In those hours 1.87% of
   transactions are fraud, against 0.114% in the other hours (about 16×). 22:00 and 23:00 alone are about 2.4%.
2. **Amount separates fraud sharply.** Median fraud amount is $341 against $49 for legit transactions. Above $300 the
   fraud rate is 8–20%; in $50–100 it is almost zero (5 of 57k). The relationship isn't monotonic (there's a
   fraud bump at $10–50), so trees should handle it better than a linear model on raw amount.
3. **Four categories carry most of the risk.** shopping_net (1.5%), grocery_pos (1.3%) and misc_net (1.3%) are about 2.5× the
   base rate, and gas_transport and shopping_pos are about at the base rate. health_fitness, food_dining, home and entertainment are under 0.2%.
4. **Distance from home is useless in Sparkov.** Merchant coordinates are jitter within about 150 km of home for
   every transaction, and the fraud rate is flat across all distance deciles (0.44–0.62%). Phase 2's
   distance features (km from last tx, impossible travel) will likely add nothing on this dataset; keep them
   for the parity and engineering story, but don't expect lift, and say so in the README.
5. **Fraud arrives in short episodes per card.** 99 of 100 cards get hit once: a median of 10 fraud transactions spread
   over about 45 h. Consecutive fraud transactions are a median 69 min apart, against 272 min between legit ones. That
   supports 1 h and 24 h velocity features, and 10 min windows less so. Almost every card being hit is a generator
   artefact; real fraud is far rarer per card.
6. **Fraud rate drifts down over time** (monthly 0.18–1.04%; Dec 2020 is the lowest at 0.18%), so train → test
   base rate goes from 0.58% to 0.35% (see Time split). Age is weak (65+ is 0.83%, 35–50 is 0.39%). Gender and day of week
   are roughly flat.

## References
- Fraud Dataset Benchmark (IEEE-CIS, Sparkov, ccfraud): https://arxiv.org/pdf/2208.14417
- Synthetic generators vs behavioural fraud patterns: https://arxiv.org/pdf/2604.13125
