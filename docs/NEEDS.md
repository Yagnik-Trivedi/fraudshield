# What You Need

## Accounts
| Account | Why | When |
|---|---|---|
| GitHub | repo + CI | now |
| Kaggle (API token) | dataset download | Phase 1 |
| (optional) Grafana Cloud / a VPS | public demo of dashboards | Phase 6 |

No paid APIs are required: everything runs locally.

## Software (Windows 11)
| Tool | Install | Used for |
|---|---|---|
| Git | `winget install Git.Git` | |
| uv | `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` | Python env + deps |
| Docker Desktop (WSL2) | `winget install Docker.DockerDesktop` | Redpanda, Redis, Postgres, Prometheus, Grafana |
| Node.js 22 LTS | `winget install OpenJS.NodeJS.LTS` | analyst console (Phase 4) |
| pre-commit | `uv tool install pre-commit` | secret scanning + lint on commit |
| kaggle CLI | `uv tool install kaggle` | dataset download |

## Hardware
- 32 GB RAM is plenty. Give Docker Desktop ≥ 6 GB (Settings → Resources).
- The GPU isn't needed (LightGBM on CPU is fast). Optional `device_type="gpu"` experiments later.

## Disk
- About 0.5 GB raw CSV, ~150 MB Parquet, plus MLflow artifacts. Keep everything under `data/` (gitignored).

## Skills you'll practise (for interviews)
Imbalanced classification, time-series-safe validation, feature engineering, calibration, Kafka
consumer groups and offsets, Redis data structures, FastAPI performance, MLflow registry, drift
statistics (PSI, Wasserstein), Prometheus metrics, workflow orchestration.
