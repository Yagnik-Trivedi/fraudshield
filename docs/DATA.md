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

## EDA findings
_(fill in during Phase 1)_

## References
- Fraud Dataset Benchmark (IEEE-CIS, Sparkov, ccfraud): https://arxiv.org/pdf/2208.14417
- Synthetic generators vs behavioural fraud patterns: https://arxiv.org/pdf/2604.13125
