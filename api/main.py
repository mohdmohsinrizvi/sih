from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

import structlog
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from connectors.registry import registry
from pipeline.processor import pipeline
from streaming.redpanda import create_topics, producer
from replay_engine.engine import replay
from synthetic.generator import SyntheticWeatherGenerator, SyntheticConfig
from metrics.prometheus import start_metrics_server, update_pipeline_metrics
from storage.database import init_db, async_session_factory
from storage.models import Report, WeatherEvent, Source, DataQuality, IngestionRun
from sqlalchemy import select, func, text

logger = structlog.get_logger(__name__)

synthetic_generator = SyntheticWeatherGenerator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_metrics_server()
    try:
        create_topics()
    except Exception as e:
        logger.warning("redpanda_unavailable", error=str(e))

    try:
        await init_db()
    except Exception as e:
        logger.warning("database_unavailable", error=str(e))

    yield

    producer.close()


app = FastAPI(
    title="National Weather Big Data Analytics Platform",
    description="SIH Problem Statement 26069 - Data Acquisition & Engineering API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "National Weather Big Data Analytics Platform",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/sources")
async def list_sources():
    return {"sources": registry.to_dict()}


@app.get("/sources/{source_id}")
async def get_source(source_id: str):
    source = registry.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return {
        "source_id": source.source_id,
        "source_name": source.source_name,
        "source_type": source.source_type,
        "enabled": source.enabled,
        "health_status": source.health_status,
    }


@app.get("/sources/health")
async def source_health():
    sources = registry.list_all()
    return {
        "total": len(sources),
        "enabled": sum(1 for s in sources if s.enabled),
        "healthy": sum(1 for s in sources if s.health_status == "healthy"),
        "sources": [{"source_id": s.source_id, "health": s.health_status} for s in sources],
    }


@app.get("/ingestion/status")
async def ingestion_status():
    return pipeline.get_status()


@app.get("/ingestion/statistics")
async def ingestion_statistics():
    return pipeline.metrics.to_dict()


@app.get("/reports")
async def list_reports(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    state: Optional[str] = None,
    city: Optional[str] = None,
    event_category: Optional[str] = None,
    quality_status: Optional[str] = None,
):
    try:
        async with async_session_factory() as session:
            query = select(Report)
            count_query = select(func.count(Report.id))

            if state:
                query = query.where(Report.state == state)
                count_query = count_query.where(Report.state == state)
            if city:
                query = query.where(Report.city == city)
                count_query = count_query.where(Report.city == city)
            if event_category:
                query = query.where(Report.event_category == event_category)
                count_query = count_query.where(Report.event_category == event_category)
            if quality_status:
                query = query.where(Report.quality_status == quality_status)
                count_query = count_query.where(Report.quality_status == quality_status)

            total = (await session.execute(count_query)).scalar() or 0
            query = query.order_by(Report.created_at.desc()).offset(offset).limit(limit)
            result = await session.execute(query)
            reports = result.scalars().all()

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "reports": [
                    {
                        "report_id": r.report_id,
                        "source_id": r.source_id,
                        "event_category": r.event_category,
                        "city": r.city,
                        "state": r.state,
                        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                        "quality_status": r.quality_status,
                        "h3_index": r.h3_index,
                        "severity": r.severity,
                        "is_simulated": r.is_simulated,
                    }
                    for r in reports
                ],
            }
    except Exception as e:
        return {"total": 0, "reports": [], "error": str(e)}


@app.get("/reports/{report_id}")
async def get_report(report_id: str):
    try:
        async with async_session_factory() as session:
            query = select(Report).where(Report.report_id == report_id)
            result = await session.execute(query)
            report = result.scalar_one_or_none()
            if not report:
                raise HTTPException(status_code=404, detail="Report not found")
            return {
                "report_id": report.report_id,
                "source_id": report.source_id,
                "source_type": report.source_type,
                "event_category": report.event_category,
                "event_subcategory": report.event_subcategory,
                "timestamp": report.timestamp.isoformat() if report.timestamp else None,
                "ingestion_timestamp": report.ingestion_timestamp.isoformat() if report.ingestion_timestamp else None,
                "text": report.text,
                "language": report.language,
                "city": report.city,
                "district": report.district,
                "state": report.state,
                "country": report.country,
                "latitude": report.latitude,
                "longitude": report.longitude,
                "hashtags": report.hashtags,
                "image_urls": report.image_urls,
                "video_urls": report.video_urls,
                "source_url": report.source_url,
                "h3_index": report.h3_index,
                "h3_resolution": report.h3_resolution,
                "temperature_celsius": report.temperature_celsius,
                "humidity_percent": report.humidity_percent,
                "rainfall_mm": report.rainfall_mm,
                "wind_speed_kmh": report.wind_speed_kmh,
                "severity": report.severity,
                "quality_status": report.quality_status,
                "quality_notes": report.quality_notes,
                "is_simulated": report.is_simulated,
                "content_hash": report.content_hash,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/candidates")
async def list_event_candidates(
    limit: int = Query(50, ge=1, le=500),
    category: Optional[str] = None,
):
    try:
        async with async_session_factory() as session:
            query = select(WeatherEvent)
            if category:
                query = query.where(WeatherEvent.event_category == category)
            query = query.order_by(WeatherEvent.created_at.desc()).limit(limit)
            result = await session.execute(query)
            events = result.scalars().all()

            return {
                "total": len(events),
                "events": [
                    {
                        "event_id": e.event_id,
                        "event_category": e.event_category,
                        "status": e.status,
                        "source_count": e.source_count,
                        "report_count": e.report_count,
                        "confidence_score": e.confidence_score,
                        "center_latitude": e.center_latitude,
                        "center_longitude": e.center_longitude,
                        "time_range_start": e.time_range_start.isoformat() if e.time_range_start else None,
                        "time_range_end": e.time_range_end.isoformat() if e.time_range_end else None,
                        "created_at": e.created_at.isoformat() if e.created_at else None,
                    }
                    for e in events
                ],
            }
    except Exception as e:
        return {"total": 0, "events": [], "error": str(e)}


@app.get("/data-quality")
async def data_quality():
    try:
        async with async_session_factory() as session:
            total = (await session.execute(select(func.count(Report.id)))).scalar() or 0
            valid = (await session.execute(
                select(func.count(Report.id)).where(Report.quality_status == "valid")
            )).scalar() or 0
            warning = (await session.execute(
                select(func.count(Report.id)).where(Report.quality_status == "warning")
            )).scalar() or 0
            invalid = (await session.execute(
                select(func.count(Report.id)).where(Report.quality_status == "invalid")
            )).scalar() or 0
            quarantined = (await session.execute(
                select(func.count(Report.id)).where(Report.quality_status == "quarantined")
            )).scalar() or 0
            pending = (await session.execute(
                select(func.count(Report.id)).where(Report.quality_status == "pending")
            )).scalar() or 0

            return {
                "total_records": total,
                "valid": valid,
                "warnings": warning,
                "invalid": invalid,
                "quarantined": quarantined,
                "pending": pending,
            }
    except Exception as e:
        return {"total_records": 0, "error": str(e)}


@app.get("/replay/status")
async def replay_status():
    return replay.stats.to_dict()


@app.post("/replay/start")
async def start_replay(
    file_path: str,
    topic: str = "weather.raw",
    speed: int = 1,
    batch_size: int = 100,
):
    stats = await replay.start(file_path, topic, speed, batch_size)
    return stats.to_dict()


@app.post("/replay/pause")
async def pause_replay():
    replay.pause()
    return replay.stats.to_dict()


@app.post("/replay/resume")
async def resume_replay():
    replay.resume()
    return replay.stats.to_dict()


@app.post("/replay/stop")
async def stop_replay():
    replay.stop()
    return replay.stats.to_dict()


@app.post("/synthetic/generate")
async def generate_synthetic(
    records: int = Query(10000, ge=1, le=1000000),
    seed: int = Query(42),
):
    config = SyntheticConfig(total_records=records, seed=seed, batch_size=1000)
    gen = SyntheticWeatherGenerator(config)

    filepath = f"data/replay/synthetic_{records}_{seed}.ndjson"
    gen.generate_to_file(filepath, records)

    return {
        "file": filepath,
        "records": records,
        "seed": seed,
        "status": "generated",
    }


@app.post("/pipeline/process-batch")
async def process_batch(reports: list[dict]):
    metrics = await pipeline.process_batch(reports)
    update_pipeline_metrics(metrics.to_dict())
    return metrics.to_dict()


@app.get("/pipeline/status")
async def pipeline_status():
    return pipeline.get_status()


@app.get("/stats/summary")
async def stats_summary():
    try:
        async with async_session_factory() as session:
            total_reports = (await session.execute(select(func.count(Report.id)))).scalar() or 0
            total_events = (await session.execute(select(func.count(WeatherEvent.id)))).scalar() or 0
            total_sources = (await session.execute(select(func.count(Source.source_id)))).scalar() or 0

            return {
                "total_reports": total_reports,
                "total_events": total_events,
                "total_sources": total_sources,
                "pipeline": pipeline.metrics.to_dict(),
                "replay": replay.stats.to_dict(),
            }
    except Exception as e:
        return {"error": str(e)}
