# Claude Code Prompts

Open Claude Code at `D:\projects\fraudshield`. It reads CLAUDE.md automatically. One task per session.
Slash commands: `/start-session`, `/next-task`, `/end-session` (in `.claude/commands/`).

## ▶ Very first session
```
Step 0: run the PowerShell commands in setup/README.md to move the Claude Code slash commands,
the CI workflow and the pre-commit config into .claude/, .github/ and the repo root, then delete setup/.
Read CLAUDE.md and docs/PLAN.md. Check git, uv and docker are installed. Run `uv sync` and `uv run pytest -q`.
Start `docker compose up -d` and confirm Redpanda Console opens at http://localhost:8080 and Redis answers PING.
Initialise git if needed, make the first commit, and give me the commands to create the GitHub repo and push.
Don't write feature code in this session.
```

## ▶ Every session
- Start: `/start-session`
- End: `/end-session`

---

## Phase 1: Data, EDA, baselines
### 1.1 Schema + loader
```
Implement fraudshield/schema.py (pydantic Transaction with the canonical fields from docs/DATA.md; drop
names/street) and fraudshield/data.py: load data/raw/fraudTrain.csv + fraudTest.csv, map columns, parse
times, compute age at transaction, sort by (event_time, trans_num), save data/processed/transactions.parquet.
Add `uv run python -m fraudshield.data --sample 0.1` that writes a card-level 10% sample. Tests use a tiny
in-memory CSV fixture, not the real files.
```
### 1.2 Synthetic generator
```
Implement fraudshield/synth.py: generate N cards × M days of transactions in the canonical schema, with
normal behaviour (home location, typical categories/amounts, daily rhythm) and injectable fraud patterns:
burst (many tx in minutes), far-away merchant, unusual amount, new category. Deterministic with a seed.
Tests check shapes, fraud rate and that patterns appear when enabled.
```
### 1.3 Time split + leakage tests
```
Add fraudshield/data.py::time_split(df, train=0.70, valid=0.15) by calendar day boundaries. Tests: no time
overlap, all cards' rows stay in order, fraud rate reported per split.
```
### 1.4 EDA notebook
```
Create notebooks/01_eda.ipynb on the 10% sample: fraud rate over time, by category, hour, amount buckets,
distance from home, age. Then summarise the 6 most useful findings in docs/DATA.md under "EDA findings".
```
### 1.5 Baselines + evaluation + MLflow
```
Implement fraudshield/evaluate.py (PR-AUC, ROC-AUC, recall at 1% FPR, precision@k, expected cost given
FN/FP costs from config; PR-curve plot) and fraudshield/train.py with three baselines on stateless features:
a rules model, logistic regression (scaled, one-hot category), LightGBM (class weights, early stopping on
validation PR-AUC). Log everything to MLflow (MLFLOW_TRACKING_URI from config). Print a Markdown results
table and paste it into README. Tests: evaluation functions on tiny known arrays; training runs on synth data
in < 30 s.
```

## Phase 2: Point-in-time features
```
Implement fraudshield/features/definitions.py (the feature list with docstrings) and features/offline.py
computing every behavioural feature point-in-time: windows are [t − w, t) per card, processing order
(event_time, trans_num); running mean/last location use only earlier events. Use pandas groupby + time-based
rolling (closed="left") or an explicit per-card loop if clearer. Tests with hand-made sequences that hit window
edges (an event exactly 10 min / 24 h earlier, ties at the same timestamp).
```
```
Retrain LightGBM with behavioural features, add isotonic calibration and cost-based thresholds (stored
with the model), SHAP global + per-transaction top-3 reasons. Register in MLflow and set alias "champion".
Update the README results table.
```

## Phase 3: Streaming
```
Implement fraudshield/features/online.py with Redis (see docs/ARCHITECTURE.md sketch) and
tests/test_feature_parity.py: generate a synthetic stream, compute offline features, then replay events in
order through the online path using fakeredis, and assert every feature matches (floats with tolerance).
```
```
Implement serving/app.py (FastAPI: /score, /health, /metrics with prometheus-client histograms, /admin/reload-model;
load models:/fraudshield@champion at startup), stream/simulator.py (replay test period at --tps; --inject-drift
amount|category|geo), stream/processor.py (consumer group, online features, score, produce predictions, write
Postgres idempotently). Bootstrap server localhost:19092 from the host. Add a Locust or simple asyncio load test
and record throughput and p50/p99 in README.
```

## Phase 4: Analyst console
```
Create SQL migrations for predictions/cases/labels/model_events (see docs/ARCHITECTURE.md). Add API endpoints
for the console (SSE live feed, cases list/detail/resolve, models). Then scaffold console/ with Next.js 16,
Tailwind, shadcn/ui, Recharts: live feed, review queue, case page (history timeline, SHAP bars, map), resolve
actions. Mobile-friendly. Playwright smoke test.
```

## Phase 5: MLOps loop
```
Add Prometheus + Grafana to docker-compose with a committed dashboard (TPS, p50/p99 latency, flag rate,
score histogram). Implement monitoring/drift.py with Evidently DataDriftPreset (reference = training window,
current = recent predictions' features), saving HTML to data/reports and a summary row in Postgres. Implement
Prefect flows: drift_check (nightly), retrain (recent labelled window), evaluate_and_promote (challenger beats
champion on PR-AUC by ≥ 0.005 and latency budget → move alias; the scoring API reloads). Tests for the promotion
decision logic. Then script the drift demo end to end.
```

## Handy prompts
- `Explain <module> like I'm in an ML interview, then give me 5 follow-up questions with answers.`
- `Review my uncommitted changes for leakage, time-split violations, and training/serving skew. List issues by severity.`
- `This fails: <error>. Write a failing test first, then fix it, then explain the root cause in 3 lines.`
