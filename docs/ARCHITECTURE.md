# Architecture

## Components
| Component | Tech | Responsibility |
|---|---|---|
| Simulator | Python + confluent-kafka | Replays test-period transactions in time order at a set TPS; can inject drift |
| Broker | Redpanda (Kafka API) | Topics `transactions`, `predictions` |
| Processor | Python consumer (later Quix Streams) | Online features → score → publish → persist |
| Online feature store | Redis | Sliding windows (sorted sets), last-seen state (hashes), seen merchants (sets) |
| Offline store | Parquet + DuckDB | Training data, point-in-time backfill |
| Model registry | MLflow (SQLite backend locally) | Versions, metrics, aliases `@champion` / `@challenger` |
| Scoring API | FastAPI + LightGBM + SHAP | `/score` → probability, decision, top reasons, model version |
| Store | Postgres | predictions, cases, labels, model_events, drift summaries |
| Console | Next.js 16 | Live feed, review queue, case page, resolve → label |
| Monitoring | Prometheus + Grafana, Evidently | Ops metrics; data and prediction drift |
| Orchestration | Prefect 3 | Drift check, retrain, evaluate, promote |

## The two feature paths (the core idea)
```
                 features/definitions.py  (names, windows, docs)
                    /                           \
   features/offline.py                    features/online.py
   pandas/DuckDB, whole history           Redis, one event at a time
   used for training                      used for scoring
                    \                           /
                  tests/test_feature_parity.py
          (same synthetic stream → identical feature values)
```
Window semantics: count events with time in `[t − w, t)`, i.e. strictly before the current event.
Processing order is `(event_time, trans_num)` in both paths. In Redis, trim with an **exclusive** bound
(`ZREMRANGEBYSCORE key -inf (t−24h`) so an event exactly 24h old is still counted, matching the offline window.

### Online feature sketch (Redis)
```python
def velocity(r, card, ts, amt, txid):
    key = f"card:{card}:tx"
    p = r.pipeline()
    p.zremrangebyscore(key, "-inf", f"({ts - 86_400}")  # keep [t-24h, ∞)
    p.zcount(key, ts - 600, f"({ts}")  # [t-10m, t)
    p.zcount(key, ts - 3_600, f"({ts}")
    p.zcount(key, ts - 86_400, f"({ts}")
    p.zadd(key, {f"{ts}:{txid}:{amt}": ts})
    p.expire(key, 90_000)
    _, c10m, c1h, c24h, *_ = p.execute()
    return {"card_tx_count_10m": c10m, "card_tx_count_1h": c1h, "card_tx_count_24h": c24h}
```

## Scoring decision
`score = calibrated P(fraud)` → `block` if ≥ T_high, `review` if ≥ T_review, else `approve`.
Thresholds come from the cost analysis on validation data and are stored with the model version.

## Data model (Postgres, Phase 4)
```sql
predictions(tx_id PK, card_id, merchant_id, amount, ts, model_version, score, decision, top_reasons jsonb, latency_ms)
cases(id PK, tx_id FK, status open|fraud|legit|escalated, assignee, notes, opened_at, closed_at)
labels(tx_id PK, is_fraud, source analyst|chargeback|dataset, labelled_at)
model_events(id PK, version, event trained|promoted|rolled_back, metrics jsonb, at)
drift_reports(id PK, window_start, window_end, dataset_drift bool, share_drifted real, report_path, at)
```

## Failure behaviour
- Redis down → score with stateless features only, mark `degraded=true`, alert.
- Model load failure → keep serving the last good model; `/health` reports it.
- Duplicate events (at-least-once delivery) → idempotent writes keyed by `tx_id`.
