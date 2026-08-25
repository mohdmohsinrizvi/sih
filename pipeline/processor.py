from __future__ import annotations

import time
import asyncio
from typing import Optional
from collections import defaultdict

import structlog

from schemas.weather_report import WeatherReport, EventCandidate, QualityStatus
from connectors.base import RawPayload, BaseConnector
from data_engine.normalization.normalizer import normalizer
from data_engine.quality.validator import validator
from data_engine.h3.indexer import indexer
from data_engine.dedup.deduplicator import deduplicator
from data_engine.event_fusion.candidate_generator import generator
from streaming.redpanda import producer, TOPICS
from storage.database import async_session_factory
from storage.models import Report, ReportRelationship, WeatherEvent, EventReport, EventCell, Source, DataQuality

logger = structlog.get_logger(__name__)


class PipelineMetrics:
    def __init__(self):
        self.records_received = 0
        self.records_normalized = 0
        self.records_validated = 0
        self.records_quarantined = 0
        self.records_stored = 0
        self.records_failed = 0
        self.duplicate_candidates = 0
        self.event_candidates = 0
        self.start_time = time.time()

    def to_dict(self) -> dict:
        elapsed = time.time() - self.start_time
        return {
            "records_received": self.records_received,
            "records_normalized": self.records_normalized,
            "records_validated": self.records_validated,
            "records_quarantined": self.records_quarantined,
            "records_stored": self.records_stored,
            "records_failed": self.records_failed,
            "duplicate_candidates": self.duplicate_candidates,
            "event_candidates": self.event_candidates,
            "elapsed_seconds": round(elapsed, 2),
            "records_per_second": round(self.records_received / elapsed, 1) if elapsed > 0 else 0,
        }


class WeatherPipeline:
    def __init__(self):
        self.metrics = PipelineMetrics()
        self._connectors: list[BaseConnector] = []
        self._running = False
        self._dedup_buffer: list[WeatherReport] = []
        self._dedup_buffer_size = 1000

    def add_connector(self, connector: BaseConnector) -> None:
        self._connectors.append(connector)

    async def start(self) -> None:
        self._running = True
        self.metrics = PipelineMetrics()
        logger.info("pipeline_started")

        tasks = [self._run_connector(conn) for conn in self._connectors]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        await self._flush_dedup_buffer()
        logger.info("pipeline_completed", metrics=self.metrics.to_dict())

    async def stop(self) -> None:
        self._running = False
        for conn in self._connectors:
            await conn.stop()
        logger.info("pipeline_stopped")

    async def _run_connector(self, connector: BaseConnector) -> None:
        await connector.start()
        try:
            async for payload in connector.fetch():
                if not self._running:
                    break
                await self.process_payload(payload)
        except Exception as e:
            logger.error("connector_error", source_id=connector.source_id, error=str(e))
        finally:
            await connector.stop()

    async def process_payload(self, payload: RawPayload) -> None:
        self.metrics.records_received += 1

        report = normalizer.normalize(payload)
        if report is None:
            self.metrics.records_failed += 1
            return

        self.metrics.records_normalized += 1

        report = validator.validate(report)
        self.metrics.records_validated += 1

        if report.quality_status == QualityStatus.INVALID:
            self.metrics.records_quarantined += 1
            await self._publish_to_topic(TOPICS["quarantine"], report)
            return

        report = indexer.index(report)

        await self._publish_to_topic(TOPICS["normalized"], report)

        if report.quality_status == QualityStatus.WARNING:
            await self._publish_to_topic(TOPICS["quarantine"], report)

        await self._store_report(report)

        self._dedup_buffer.append(report)
        if len(self._dedup_buffer) >= self._dedup_buffer_size:
            await self._flush_dedup_buffer()

    @staticmethod
    def _strip_tz(dt):
        if dt is not None and dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt

    async def _store_report(self, report: WeatherReport) -> None:
        try:
            async with async_session_factory() as session:
                db_report = Report(
                    report_id=report.report_id,
                    source_id=report.source_id,
                    source_type=report.source_type.value,
                    event_category=report.event_category.value,
                    event_subcategory=report.event_subcategory,
                    timestamp=self._strip_tz(report.timestamp),
                    ingestion_timestamp=self._strip_tz(report.ingestion_timestamp),
                    text=report.text,
                    language=report.language,
                    city=report.city,
                    district=report.district,
                    state=report.state,
                    country=report.country,
                    latitude=report.latitude,
                    longitude=report.longitude,
                    hashtags=report.hashtags,
                    image_urls=report.image_urls,
                    video_urls=report.video_urls,
                    source_url=report.source_url,
                    author_id_hash=report.author_id_hash,
                    raw_payload_reference=report.raw_payload_reference,
                    is_simulated=report.is_simulated,
                    schema_version=report.schema_version,
                    h3_index=report.h3_index,
                    h3_resolution=report.h3_resolution,
                    temperature_celsius=report.temperature_celsius,
                    humidity_percent=report.humidity_percent,
                    rainfall_mm=report.rainfall_mm,
                    wind_speed_kmh=report.wind_speed_kmh,
                    wind_direction=report.wind_direction,
                    pressure_hpa=report.pressure_hpa,
                    visibility_km=report.visibility_km,
                    severity=report.severity,
                    quality_status=report.quality_status.value,
                    quality_notes=report.quality_notes,
                    content_hash=report.content_hash,
                    extra_metadata=report.extra_metadata,
                )
                if report.latitude and report.longitude:
                    from geoalchemy2.elements import WKTElement
                    db_report.location = WKTElement(f"POINT({report.longitude} {report.latitude})", srid=4326)

                session.add(db_report)
                await session.commit()
                self.metrics.records_stored += 1
        except Exception as e:
            logger.error("store_report_failed", report_id=report.report_id, error=str(e))
            self.metrics.records_failed += 1

    async def _flush_dedup_buffer(self) -> None:
        if not self._dedup_buffer:
            return

        reports = self._dedup_buffer.copy()
        self._dedup_buffer.clear()

        relationships = deduplicator.generate_candidates(reports)
        self.metrics.duplicate_candidates += len(relationships)

        for rel in relationships:
            await self._publish_to_topic(TOPICS["dedup"], {
                "relationship_id": rel.relationship_id,
                "report_id_a": rel.report_id_a,
                "report_id_b": rel.report_id_b,
                "relationship_type": rel.relationship_type,
                "confidence": rel.confidence,
                "metadata": rel.metadata,
            })

        candidates = generator.generate_candidates(reports)
        self.metrics.event_candidates += len(candidates)

        for candidate in candidates:
            await self._publish_to_topic(TOPICS["events"], candidate.model_dump(mode="json"))

        logger.info(
            "dedup_flush",
            reports=len(reports),
            relationships=len(relationships),
            event_candidates=len(candidates),
        )

    async def _publish_to_topic(self, topic: str, data: dict) -> None:
        try:
            if isinstance(data, WeatherReport):
                key = data.to_redpanda_key()
                value = data.to_dict()
            else:
                key = data.get("report_id", data.get("candidate_event_id", ""))
                value = data

            await producer.produce_async(topic, key, value)
        except Exception as e:
            logger.error("publish_failed", topic=topic, error=str(e))

    async def process_batch(self, reports: list[dict]) -> PipelineMetrics:
        self.metrics = PipelineMetrics()

        for report_data in reports:
            payload = RawPayload(
                source_id=report_data.get("source_id", "batch"),
                source_type=report_data.get("source_type", "batch"),
                content=report_data,
            )
            await self.process_payload(payload)

        await self._flush_dedup_buffer()
        return self.metrics

    def get_status(self) -> dict:
        return {
            "running": self._running,
            "metrics": self.metrics.to_dict(),
            "connectors": len(self._connectors),
            "dedup_buffer_size": len(self._dedup_buffer),
        }


pipeline = WeatherPipeline()
