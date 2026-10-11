from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration via environment variables / .env (see .env.example)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Data
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    random_seed: int = 42

    # Evaluation / decision costs (illustrative; document assumptions in README)
    fn_cost: float = 5000.0  # missed fraud, in INR
    fp_cost: float = 50.0  # analyst review / customer friction, in INR
    analyst_capacity_per_day: int = 200

    # Infra
    kafka_bootstrap: str = "localhost:19092"
    topic_transactions: str = "transactions"
    topic_predictions: str = "predictions"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql://fraudshield:fraudshield@localhost:5433/fraudshield"
    mlflow_tracking_uri: str = "http://127.0.0.1:5000"
    model_name: str = "fraudshield"

    # Serving
    score_latency_budget_ms: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
