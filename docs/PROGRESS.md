# Progress Log

Newest entry on top.

---

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
- Docker Desktop not installed: compose (Redpanda Console, Redis PING) not verified yet. Not needed until Phase 3.

## 2026-10-11: Project started (Phase 0)
**Done**
- Repo skeleton: pyproject (uv), MIT license, `.gitignore`, `.env.example`, docker-compose (Redpanda + Console, Redis, Postgres), CI (ruff + pytest + gitleaks), pre-commit
- Docs: CLAUDE.md, PLAN (zero → v1.0 with dates), DATA, NEEDS, ARCHITECTURE, PROMPTS, decisions
- `fraudshield/config.py` + smoke test

**Next (Phase 1, light mode until Oct 31)**
- Push to GitHub; Kaggle token; download Sparkov; PROMPTS 1.1 (schema + loader)

**Notes**
- DocuMind has priority until its Phase 2 ends (~Oct 28); FraudShield runs in light mode until Oct 31
