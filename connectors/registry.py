from __future__ import annotations

import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)

SOURCES_FILE = Path("config/sources.yaml")


@dataclass
class SourceConfig:
    source_id: str
    source_name: str
    source_type: str
    url: Optional[str] = None
    connector_type: str = "rest_api"
    authentication_required: bool = False
    poll_interval_seconds: int = 0
    reliability: float = 0.5
    geographic_coverage: str = "India"
    rate_limits: Optional[str] = None
    enabled: bool = True
    legal_notes: Optional[str] = None
    update_frequency: Optional[str] = None
    description: Optional[str] = None
    last_successful_fetch: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    health_status: str = "unknown"
    extra_metadata: dict = field(default_factory=dict)


class SourceRegistry:
    def __init__(self, sources_file: Optional[Path] = None):
        self._sources_file = sources_file or SOURCES_FILE
        self._sources: dict[str, SourceConfig] = {}
        self._load()

    def _load(self) -> None:
        if not self._sources_file.exists():
            logger.warning("sources_file_not_found", path=str(self._sources_file))
            return

        with open(self._sources_file, "r") as f:
            data = yaml.safe_load(f)

        for src in data.get("sources", []):
            config = SourceConfig(**src)
            self._sources[config.source_id] = config

        logger.info("sources_loaded", count=len(self._sources))

    def get(self, source_id: str) -> Optional[SourceConfig]:
        return self._sources.get(source_id)

    def list_all(self) -> list[SourceConfig]:
        return list(self._sources.values())

    def list_enabled(self) -> list[SourceConfig]:
        return [s for s in self._sources.values() if s.enabled]

    def register(self, config: SourceConfig) -> None:
        self._sources[config.source_id] = config
        logger.info("source_registered", source_id=config.source_id)

    def update_health(self, source_id: str, status: str) -> None:
        if source_id in self._sources:
            self._sources[source_id].health_status = status
            if status == "healthy":
                self._sources[source_id].last_successful_fetch = datetime.utcnow()
            elif status == "error":
                self._sources[source_id].last_failure = datetime.utcnow()

    def to_dict(self) -> list[dict]:
        return [
            {
                "source_id": s.source_id,
                "source_name": s.source_name,
                "source_type": s.source_type,
                "connector_type": s.connector_type,
                "enabled": s.enabled,
                "reliability": s.reliability,
                "health_status": s.health_status,
                "last_successful_fetch": s.last_successful_fetch.isoformat() if s.last_successful_fetch else None,
                "last_failure": s.last_failure.isoformat() if s.last_failure else None,
            }
            for s in self._sources.values()
        ]


registry = SourceRegistry()
