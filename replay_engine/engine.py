from __future__ import annotations

import asyncio
import time
from typing import Optional
from pathlib import Path
from dataclasses import dataclass, field

import orjson
import structlog

from streaming.redpanda import producer, TOPICS

logger = structlog.get_logger(__name__)


@dataclass
class ReplayStats:
    records_sent: int = 0
    records_failed: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    elapsed_seconds: float = 0.0
    records_per_second: float = 0.0
    topic: str = ""
    file_path: str = ""
    speed: int = 1
    status: str = "idle"

    def to_dict(self) -> dict:
        return {
            "records_sent": self.records_sent,
            "records_failed": self.records_failed,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "records_per_second": round(self.records_per_second, 1),
            "topic": self.topic,
            "file_path": self.file_path,
            "speed": self.speed,
            "status": self.status,
        }


class ReplayEngine:
    def __init__(self):
        self._stats = ReplayStats()
        self._paused = False
        self._stopped = False
        self._task: Optional[asyncio.Task] = None

    async def start(
        self,
        file_path: str,
        topic: str = "weather.raw",
        speed: int = 1,
        batch_size: int = 100,
    ) -> ReplayStats:
        if self._task and not self._task.done():
            logger.warning("replay_already_running")
            return self._stats

        self._paused = False
        self._stopped = False
        self._stats = ReplayStats(
            file_path=file_path,
            topic=topic,
            speed=speed,
            status="running",
            start_time=time.time(),
        )

        self._task = asyncio.create_task(self._run(file_path, topic, speed, batch_size))
        return self._stats

    async def _run(self, file_path: str, topic: str, speed: int, batch_size: int) -> None:
        path = Path(file_path)
        if not path.exists():
            logger.error("replay_file_not_found", path=file_path)
            self._stats.status = "error"
            return

        logger.info("replay_started", file=file_path, topic=topic, speed=speed)

        try:
            with open(path, "rb") as f:
                batch = []

                for line_num, line in enumerate(f, 1):
                    if self._stopped:
                        break

                    while self._paused:
                        await asyncio.sleep(0.1)
                        if self._stopped:
                            return

                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = orjson.loads(line)
                        batch.append(data)

                        if len(batch) >= batch_size:
                            await self._send_batch(batch, topic)
                            batch = []

                            if speed > 1:
                                delay = batch_size / (speed * 100)
                                await asyncio.sleep(min(delay, 1.0))

                    except Exception as e:
                        self._stats.records_failed += 1
                        logger.warning("replay_line_error", line=line_num, error=str(e))

                if batch:
                    await self._send_batch(batch, topic)

        except Exception as e:
            logger.error("replay_error", error=str(e))
            self._stats.status = "error"
            return

        self._stats.end_time = time.time()
        self._stats.elapsed_seconds = self._stats.end_time - self._stats.start_time
        self._stats.records_per_second = (
            self._stats.records_sent / self._stats.elapsed_seconds
            if self._stats.elapsed_seconds > 0 else 0
        )
        self._stats.status = "completed"

        logger.info("replay_completed", stats=self._stats.to_dict())

    async def _send_batch(self, batch: list[dict], topic: str) -> None:
        for record in batch:
            try:
                key = record.get("source_id", "replay")
                await producer.produce_async(topic, key, record)
                self._stats.records_sent += 1
            except Exception as e:
                self._stats.records_failed += 1
                logger.warning("replay_send_failed", error=str(e))

    def pause(self) -> None:
        self._paused = True
        self._stats.status = "paused"
        logger.info("replay_paused")

    def resume(self) -> None:
        self._paused = False
        self._stats.status = "running"
        logger.info("replay_resumed")

    def stop(self) -> None:
        self._stopped = True
        self._stats.status = "stopped"
        logger.info("replay_stopped")

    @property
    def stats(self) -> ReplayStats:
        if self._stats.start_time and self._stats.status in ("running", "paused"):
            self._stats.elapsed_seconds = time.time() - self._stats.start_time
            if self._stats.elapsed_seconds > 0:
                self._stats.records_per_second = self._stats.records_sent / self._stats.elapsed_seconds
        return self._stats


replay = ReplayEngine()
