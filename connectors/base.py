from __future__ import annotations

import abc
import time
from typing import AsyncIterator, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

import structlog
import httpx

from schemas.weather_report import WeatherReport, SourceType
from connectors.registry import SourceConfig

logger = structlog.get_logger(__name__)


@dataclass
class RawPayload:
    source_id: str
    source_type: str
    content: dict | list | str
    content_type: str = "application/json"
    url: Optional[str] = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    checksum: Optional[str] = None
    schema_version: str = "1.0"
    extra_metadata: dict = field(default_factory=dict)


class BaseConnector(abc.ABC):
    def __init__(self, source_config: SourceConfig):
        self.source_config = source_config
        self.source_id = source_config.source_id
        self._running = False
        self._stats = {
            "records_fetched": 0,
            "records_failed": 0,
            "total_requests": 0,
            "failed_requests": 0,
            "start_time": None,
        }

    @abc.abstractmethod
    async def fetch(self) -> AsyncIterator[RawPayload]:
        """Fetch data from the source. Yields RawPayload objects."""
        ...

    async def start(self) -> None:
        self._running = True
        self._stats["start_time"] = datetime.now(timezone.utc)
        logger.info("connector_started", source_id=self.source_id)

    async def stop(self) -> None:
        self._running = False
        logger.info("connector_stopped", source_id=self.source_id, stats=self._stats)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def stats(self) -> dict:
        return dict(self._stats)


class RestAPIConnector(BaseConnector):
    """Generic REST API connector with retries and backoff."""

    def __init__(self, source_config: SourceConfig, api_key: Optional[str] = None):
        super().__init__(source_config)
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers=headers,
                follow_redirects=True,
            )
        return self._client

    async def fetch(self) -> AsyncIterator[RawPayload]:
        client = await self._get_client()
        max_retries = 5
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                self._stats["total_requests"] += 1
                url = self.source_config.url
                if not url:
                    logger.warning("no_url_configured", source_id=self.source_id)
                    return

                response = await client.get(url)
                response.raise_for_status()

                content = response.json()
                self._stats["records_fetched"] += 1

                yield RawPayload(
                    source_id=self.source_id,
                    source_type=self.source_config.source_type,
                    content=content,
                    url=str(response.url),
                )
                return

            except httpx.HTTPStatusError as e:
                self._stats["failed_requests"] += 1
                logger.warning(
                    "api_http_error",
                    source_id=self.source_id,
                    status=e.response.status_code,
                    attempt=attempt + 1,
                )
            except (httpx.RequestError, Exception) as e:
                self._stats["failed_requests"] += 1
                logger.warning(
                    "api_request_error",
                    source_id=self.source_id,
                    error=str(e),
                    attempt=attempt + 1,
                )

            if attempt < max_retries - 1:
                delay = min(base_delay * (2 ** attempt), 30.0)
                await self._async_sleep(delay)

        self._stats["records_failed"] += 1
        logger.error("connector_fetch_failed", source_id=self.source_id, max_retries=max_retries)

    async def _async_sleep(self, seconds: float) -> None:
        import asyncio
        await asyncio.sleep(seconds)

    async def stop(self) -> None:
        await super().stop()
        if self._client and not self._client.is_closed:
            await self._client.aclose()


class JsonFileConnector(BaseConnector):
    """Connector for local JSON files."""

    def __init__(self, source_config: SourceConfig, file_path: str):
        super().__init__(source_config)
        self.file_path = file_path

    async def fetch(self) -> AsyncIterator[RawPayload]:
        import json
        from pathlib import Path

        path = Path(self.file_path)
        if not path.exists():
            logger.error("file_not_found", path=self.file_path)
            return

        with open(path, "r") as f:
            data = json.load(f)

        if isinstance(data, list):
            for item in data:
                self._stats["records_fetched"] += 1
                yield RawPayload(
                    source_id=self.source_id,
                    source_type=self.source_config.source_type,
                    content=item,
                )
        else:
            self._stats["records_fetched"] += 1
            yield RawPayload(
                source_id=self.source_id,
                source_type=self.source_config.source_type,
                content=data,
            )


class CSVFileConnector(BaseConnector):
    """Connector for CSV files using Polars."""

    def __init__(self, source_config: SourceConfig, file_path: str):
        super().__init__(source_config)
        self.file_path = file_path

    async def fetch(self) -> AsyncIterator[RawPayload]:
        import polars as pl
        from pathlib import Path

        path = Path(self.file_path)
        if not path.exists():
            logger.error("file_not_found", path=self.file_path)
            return

        df = pl.read_csv(str(path))

        for row in df.iter_rows(named=True):
            self._stats["records_fetched"] += 1
            yield RawPayload(
                source_id=self.source_id,
                source_type=self.source_config.source_type,
                content=dict(row),
            )


class NDJSONFileConnector(BaseConnector):
    """Connector for newline-delimited JSON files."""

    def __init__(self, source_config: SourceConfig, file_path: str):
        super().__init__(source_config)
        self.file_path = file_path

    async def fetch(self) -> AsyncIterator[RawPayload]:
        import orjson
        from pathlib import Path

        path = Path(self.file_path)
        if not path.exists():
            logger.error("file_not_found", path=self.file_path)
            return

        with open(path, "rb") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = orjson.loads(line)
                    self._stats["records_fetched"] += 1
                    yield RawPayload(
                        source_id=self.source_id,
                        source_type=self.source_config.source_type,
                        content=data,
                    )
                except Exception as e:
                    self._stats["records_failed"] += 1
                    logger.warning("ndjson_parse_error", error=str(e))


class CitizenReportConnector(BaseConnector):
    """Connector for citizen-submitted reports via API endpoint."""

    def __init__(self, source_config: SourceConfig):
        super().__init__(source_config)
        self._pending_reports: list[dict] = []

    def submit_report(self, report_data: dict) -> None:
        self._pending_reports.append(report_data)

    async def fetch(self) -> AsyncIterator[RawPayload]:
        while self._pending_reports:
            report = self._pending_reports.pop(0)
            self._stats["records_fetched"] += 1
            yield RawPayload(
                source_id=self.source_id,
                source_type="citizen",
                content=report,
            )


class ReplayConnector(BaseConnector):
    """Connector for replaying recorded data at configurable speeds."""

    def __init__(self, source_config: SourceConfig, file_path: str, speed: int = 1):
        super().__init__(source_config)
        self.file_path = file_path
        self.speed = speed
        self._paused = False
        self._stopped = False
        self._records_sent = 0
        self._start_timestamp: Optional[float] = None
        self._pause_event = None

    async def fetch(self) -> AsyncIterator[RawPayload]:
        import orjson
        from pathlib import Path

        path = Path(self.file_path)
        if not path.exists():
            logger.error("replay_file_not_found", path=self.file_path)
            return

        self._start_timestamp = time.time()

        with open(path, "rb") as f:
            for line in f:
                if self._stopped:
                    break

                while self._paused:
                    import asyncio
                    await asyncio.sleep(0.1)
                    if self._stopped:
                        return

                line = line.strip()
                if not line:
                    continue

                try:
                    data = orjson.loads(line)
                    self._stats["records_fetched"] += 1
                    self._records_sent += 1

                    yield RawPayload(
                        source_id=data.get("source_id", self.source_id),
                        source_type=data.get("source_type", "replay"),
                        content=data,
                        extra_metadata={"replay_speed": self.speed, "replay_sequence": self._records_sent},
                    )

                    if self.speed > 0 and "_timestamp" in data:
                        import asyncio
                        ts = data["_timestamp"]
                        if isinstance(ts, (int, float)) and self._start_timestamp:
                            target_delay = ts / self.speed
                            elapsed = time.time() - self._start_timestamp
                            sleep_time = max(0, target_delay - elapsed)
                            if sleep_time > 0:
                                await asyncio.sleep(min(sleep_time, 1.0))

                except Exception as e:
                    self._stats["records_failed"] += 1
                    logger.warning("replay_parse_error", error=str(e))

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def stop(self) -> None:
        self._stopped = True

    @property
    def records_sent(self) -> int:
        return self._records_sent


CONNECTOR_MAP = {
    "rest_api": RestAPIConnector,
    "json": JsonFileConnector,
    "csv": CSVFileConnector,
    "ndjson": NDJSONFileConnector,
    "citizen": CitizenReportConnector,
    "replay": ReplayConnector,
}


def create_connector(source_config: SourceConfig, **kwargs) -> BaseConnector:
    connector_cls = CONNECTOR_MAP.get(source_config.connector_type)
    if connector_cls is None:
        raise ValueError(f"Unknown connector type: {source_config.connector_type}")
    return connector_cls(source_config, **kwargs)
