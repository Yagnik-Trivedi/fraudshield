# CLAUDE.md: instructions for Claude Code in this repo

Read this first in every session, then `docs/PROGRESS.md` and the current phase of `docs/PLAN.md`.
When a task is done: tick it in PLAN.md, add a dated entry to PROGRESS.md, update "Current status" below.

## What this project is
**FraudShield**: a real-time card-fraud detection system with a full MLOps loop. Transactions are
replayed from a public dataset into a Kafka-compatible stream (Redpanda). Behavioural features are kept
in Redis, and a LightGBM model (versioned in MLflow) scores each transaction in milliseconds, with SHAP
reasons. Flagged cases go to a Next.js analyst console, and analyst decisions become labels. Drift is
monitored with Evidently, and Prefect retrains a challenger and promotes it only if it beats the champion.

It's a solo resume project for Yagnik (3rd-year CS, aiming at SDE + AI/ML roles). The goal is a
project he can **explain deeply in interviews**, with **honest measured numbers**.

## Non-negotiable ML rules
1. **Time-based splits only.** Never random-split transactions. Train < validation < test in time.
2. **Point-in-time features.** A feature for a transaction at time t may only use events strictly before t
   (`[t - window, t)` for windows). The SAME feature definitions serve offline training and online
   scoring. A parity test must prove offline == online on a sample.
3. **No label leakage.** Don't use columns that encode the outcome. Target encodings are fit on train only.
4. **Metrics:** PR-AUC is primary (ROC-AUC is misleading at <1% fraud), plus recall at fixed FPR,
   precision@k and expected cost. Never report accuracy as the headline.
5. **Synthetic-data honesty:** the dataset is simulated; never claim real-world performance.

## Engineering rules
- Python 3.11+, managed with **uv**. Package code in `fraudshield/`, tests in `tests/`.
- Config only via `fraudshield/config.py` (pydantic-settings) and `.env`. No secrets in git (gitleaks runs in pre-commit and CI).
- Every feature needs tests; `uv run pytest -q` and `uv run ruff check .` must pass before a task counts as done.
- Tests must not need Docker or the full dataset: use the synthetic generator and `fakeredis`.
- Keep code readable over clever. New libraries need a line in `docs/decisions.md`.
- Raw data lives in `data/` (gitignored). Never commit datasets or model binaries.
- The user is on **Windows 11** (PowerShell, Docker Desktop, 32 GB RAM, RTX 5060). Give Windows-friendly commands.
- Small, conventional commits (`feat(features): …`). Don't push unless asked.
- Only work on the current phase. Park ideas in "Later" at the bottom of PLAN.md.

## Target layout (create as phases progress)
```
fraudshield/
  config.py          settings
  schema.py          canonical Transaction model + Sparkov column mapping
  data.py            load raw CSV -> parquet; time split
  synth.py           small synthetic generator in the same schema (tests, demos)
  features/
    definitions.py   feature list + docs (single source of truth)
    offline.py       point-in-time features with pandas/DuckDB
    online.py        the same features, incremental, on Redis
  train.py           baselines + LightGBM, calibration, threshold by cost, MLflow logging
  evaluate.py        metrics, plots, champion vs challenger
  serving/app.py     FastAPI /score, /health, /metrics
  stream/            simulator (producer) + processor (consumer -> score -> produce)
  monitoring/        Evidently drift job
  pipelines/         Prefect flows: drift check, retrain, promote
console/             Next.js analyst console (Phase 4)
infra/               prometheus.yml, grafana dashboards
tests/
notebooks/           EDA only; real logic lives in the package
```

## Commands
```bash
uv sync                                   # install
uv run pytest -q                          # tests
uv run ruff check . ; uv run ruff format .
docker compose up -d                      # redpanda, console (localhost:8080), redis, postgres
uv run mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///data/mlflow.db --default-artifact-root ./data/mlartifacts
```

## Current status (update when it changes)
Phase 1 in progress: 1.1 loader, 1.2 synth, 1.3 time split, 1.4 EDA done; data loaded; infra up. Next: 1.5 baselines + evaluate + MLflow.
