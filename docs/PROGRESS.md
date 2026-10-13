# Progress Log

Newest entry on top.

---

## 2026-10-13: Phase 1 · 1.3 time split
**Done**
- `data.time_split` (calendar-day boundaries, 70/15/15) + `split_summary`; the loader prints the split table
- `tests/test_split.py` (5 tests on synth data): no overlap, day boundaries, lossless + ordered, fraud rate, too-few-days error; suite 22 passed
- Real data: train 0.579% → valid 0.468% → test 0.350% fraud (table in DATA.md)

**Next**
- 1.4 EDA notebook (needs the `notebooks` extra: `uv sync --extra notebooks`)

## 2026-10-11: Phase 1 · infra verified, data loaded, 1.2 synthetic generator
**Done**
- Docker Desktop + WSL2 installed; `docker compose up -d`: Redis PONG, Postgres ready, Console HTTP 200, Redpanda healthy
- Real data loaded: 1,852,394 rows, 999 cards, 0.521% fraud (details in DATA.md)
- `synth.py`: cards with home location, habitual categories, spend level, daily rhythm; fraud patterns
  burst / far_away / unusual_amount / new_category; deterministic by seed; emits Sparkov columns → `to_canonical`
- `tests/test_synth.py` (8 tests); suite 17 passed

**Next**
- 1.3 time split + leakage tests

**Open issues**
- Compose images still use `latest` tags; pin them once stable

## 2026-10-11: Phase 1 · 1.1 schema + loader
**Done**
- `schema.py`: pydantic `Transaction` + Sparkov→canonical column map (tx_id, card_id, merchant_id, amount, lon...)
- `data.py`: raw CSVs → canonical, sorted by (event_time, tx_id) → `transactions.parquet`; `--sample 0.1` card-level sample
- `tests/test_data.py` (6 tests, in-memory CSV fixture)

**Next**
- Kaggle token + download Sparkov, then `uv run python -m fraudshield.data --sample 0.1`; 1.2 synthetic generator

## 2026-10-11: First session (setup)
**Done**
- Moved `setup/` files into `.claude/commands/`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`; deleted `setup/`
- `uv sync` OK; `uv run pytest -q` 3 passed; ruff clean
- `git init` + first commit

**Open issues**
- ~~Docker Desktop not installed~~ (resolved same day)

## 2026-10-11: Project started (Phase 0)
**Done**
- Repo skeleton: pyproject (uv), MIT license, `.gitignore`, `.env.example`, docker-compose (Redpanda + Console, Redis, Postgres), CI (ruff + pytest + gitleaks), pre-commit
- Docs: CLAUDE.md, PLAN (zero → v1.0 with dates), DATA, NEEDS, ARCHITECTURE, PROMPTS, decisions
- `fraudshield/config.py` + smoke test

**Next (Phase 1, light mode until Oct 31)**
- Push to GitHub; Kaggle token; download Sparkov; PROMPTS 1.1 (schema + loader)

**Notes**
- DocuMind has priority until its Phase 2 ends (~Oct 28); FraudShield runs in light mode until Oct 31
