# FraudShield: Plan from Zero to Complete

**Start:** Sun Oct 11, 2026 · **Complete (v1.0):** Sun Jan 10, 2027

**Pacing.** DocuMind is the priority project (its core and eval phases end ~Oct 28). Until Oct 31 FraudShield runs in **light
mode** (about 2 sessions a week, offline ML only, no infra). From Nov 1 it runs at full pace alongside
DocuMind's resume track. Leave slack around end-semester exams. If exams land in this window, shift
the dates and keep the order.

Tick boxes as you go. Claude Code: only the current phase; ideas go to "Later".

---

## Definition of complete (v1.0)
- [ ] `docker compose up` + one command starts the simulator; transactions flow end to end
- [ ] Online features in Redis match offline features (parity test in CI)
- [ ] LightGBM champion in the MLflow registry; scoring API p99 < 30 ms on a laptop at ≥ 200 tx/s
- [ ] Results table with rules → logistic regression → LightGBM → +behavioural features (time-split test set)
- [ ] Analyst console: live feed, review queue, case page with SHAP reasons, resolve → label
- [ ] Grafana dashboard (TPS, latency percentiles, flag rate, score distribution)
- [ ] Nightly Evidently drift report; Prefect flow retrains and promotes only when the challenger wins
- [ ] Recorded demo: inject drift → detected → retrain → promoted → flag rate recovers
- [ ] README with architecture, results, limitations; blog post; resume bullets filled with real numbers

---

## Phase 0: Foundation ✅ (Sun Oct 11)
- [x] Repo, MIT license, `.gitignore`, `.env.example`, pyproject (uv), docker-compose (Redpanda, Console, Redis, Postgres), CI, pre-commit, CLAUDE.md, docs
- [x] **Yagnik:** create the GitHub repo and push; run the "Very first session" prompt in PROMPTS.md

## Phase 1: Data, EDA, baselines (Oct 12 – Oct 31, light mode, ~5 sessions)
Goal: an honest offline baseline with leak-free evaluation.
- [x] Kaggle account + API token; download Sparkov (`docs/DATA.md`) into `data/raw/`
- [x] `fraudshield/schema.py`: canonical `Transaction` (pydantic) + Sparkov column mapping; `data.py` converts CSV → Parquet with dtypes
- [x] `synth.py`: a tiny generator in the same schema with injectable fraud patterns (bursts, far-away merchant, unusual amount) for tests
- [x] EDA notebook: fraud rate over time, by category/hour/amount; findings written to `docs/DATA.md`
- [x] Time split: train / validation / test by `trans_time` (e.g. first 70% of days / next 15% / last 15%), with a test asserting no overlap
- [ ] Baselines on **stateless** features (amount, hour, day-of-week, category, age, city_pop): rules, logistic regression, LightGBM
- [ ] `evaluate.py`: PR-AUC, ROC-AUC (secondary), recall@1%FPR, precision@k (k = daily analyst capacity), PR curve plot
- [ ] MLflow tracking (local server, SQLite backend) logging params, metrics, plots, model
- **Exit check:** the results table has three rows with numbers on the time-split test set.

## Phase 2: Point-in-time features + strong model (Nov 1 – Nov 14)
- [ ] `features/definitions.py`: one documented list of features (velocity counts 10m/1h/24h, amount sum 1h, secs since last tx, km from last tx, impossible-travel flag, amount vs card's running mean, new merchant for card, category risk (train-fit target encoding))
- [ ] `features/offline.py`: point-in-time computation (pandas/DuckDB), windows `[t − w, t)`
- [ ] LightGBM with behavioural features; class weights; early stopping on validation PR-AUC
- [ ] Calibration (isotonic) + cost-based threshold (FN cost vs FP cost, documented assumptions)
- [ ] SHAP global importance plot + per-transaction top-3 reasons function
- [ ] Register the model in MLflow and set alias `champion`
- **Exit check:** the results table shows the lift from behavioural features; leakage tests pass.

## Phase 3: Streaming + online features + scoring (Nov 15 – Nov 28)
- [ ] `features/online.py`: the same features on Redis (sorted sets for windows, hashes for last location/running mean, sets for seen merchants)
- [ ] **Parity test:** for a synthetic stream, online features == offline features for every transaction (fakeredis)
- [ ] `serving/app.py`: FastAPI `/score` (loads `models:/fraudshield@champion`), `/health`, `/metrics` (Prometheus), `/admin/reload-model`
- [ ] `stream/simulator.py`: replay test-period transactions in time order at `--tps`, with `--inject-drift` options
- [ ] `stream/processor.py`: consume `transactions` → online features → score → produce `predictions` → write Postgres (idempotent on tx id)
- [ ] Load test: sustained tx/s and p50/p99 scoring latency on the laptop; numbers in README
- **Exit check:** the simulator at 200 tx/s runs for 10 minutes with stable latency and the parity test is green in CI.

## Phase 4: Analyst console (Nov 29 – Dec 12)
- [ ] Postgres tables: predictions, cases, labels, model_events (SQL migration)
- [ ] API: `/stream/predictions` (SSE), `/cases`, `/cases/{id}`, `/cases/{id}/resolve`, `/models`
- [ ] `console/` (Next.js 16 + Tailwind + shadcn/ui + Recharts): live feed, queue sorted by score, case page (card's recent history timeline, SHAP bar chart, map of last locations), approve / confirm fraud
- [ ] Auth for the console (Better Auth; roles analyst / admin)
- **Exit check:** a flagged transaction can be reviewed and resolved; the label lands in `labels`.

## Phase 5: MLOps loop (Dec 13 – Dec 31)
- [ ] Prometheus + Grafana in compose; dashboard JSON committed in `infra/`
- [ ] `monitoring/drift.py`: Evidently `DataDriftPreset` (reference = training window, current = last N hours) → HTML + JSON summary in Postgres
- [ ] Prefect flows: nightly drift check; retrain on recent labelled window; evaluate challenger vs champion on the latest labelled week; promote by moving the MLflow alias only if PR-AUC improves by ≥ 0.005 and p99 latency stays within budget; scoring API hot-reloads
- [ ] Shadow mode: the challenger scores in parallel; only logged
- [ ] Drift demo: inject new merchant categories / inflated amounts → detection → retrain → promotion; record a 2-minute video
- **Exit check:** the end-to-end loop runs unattended in the demo.

## Phase 6: Ship v1.0 (Jan 1 – Jan 10, 2027)
- [ ] Second benchmark on IEEE-CIS (offline only) for the README
- [ ] README final: results table, Grafana screenshots, architecture, limitations, how to reproduce
- [ ] Blog post: "Training/serving skew: how I proved my fraud features match online and offline"
- [ ] Fill the resume bullets (TODOP/02-FraudShield) with measured numbers; tag `v1.0.0`

---

## Risks
| Risk | Mitigation |
|---|---|
| DocuMind/exams eat the time | Light mode until Oct 31; the phase order matters more than the dates |
| Kafka/Redpanda on Windows Docker quirks | Use the advertised listener config in docker-compose; the processor connects to `localhost:19092` from the host |
| Dataset too big for quick iteration | Develop on a 10% sample (by card, not by row); full runs only for reported numbers |
| Parity test fails at window edges | Windows are `[t − w, t)`; Redis trims with exclusive bounds; same tie-break order (time, then tx id) |
| Over-engineering | Each phase has an exit check; nothing from "Later" before v1.0 |

## Later (parking lot)
- Graph features (shared merchant/device rings), GNN
- Exactly-once with Kafka transactions
- Feast as a formal feature store
- Kubernetes (k3s) + Helm deployment
- Autoencoder anomaly score as an extra feature
