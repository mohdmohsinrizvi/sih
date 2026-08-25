from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://weather:weather@localhost:5432/weatherdb"
    DATABASE_URL_SYNC: str = "postgresql://weather:weather@localhost:5432/weatherdb"
    REDIS_URL: str = "redis://localhost:6379/0"
    REDPANDA_BOOTSTRAP_SERVERS: str = "localhost:19092"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "weather-data"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DATA_DIR: str = "./data"
    SCHEMA_VERSION: str = "1.0"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
