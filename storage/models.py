from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, Enum as SAEnum, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector

from storage.database import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class Source(Base):
    __tablename__ = "sources"

    source_id = Column(String, primary_key=True)
    source_name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    url = Column(String, nullable=True)
    connector_type = Column(String, nullable=False)
    authentication_required = Column(Boolean, default=False)
    poll_interval_seconds = Column(Integer, default=0)
    reliability = Column(Float, default=0.5)
    geographic_coverage = Column(String, default="India")
    rate_limits = Column(String, nullable=True)
    enabled = Column(Boolean, default=True)
    legal_notes = Column(Text, nullable=True)
    update_frequency = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    last_successful_fetch = Column(DateTime, nullable=True)
    last_failure = Column(DateTime, nullable=True)
    health_status = Column(String, default="unknown")
    extra_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    reports = relationship("Report", back_populates="source")


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(String, unique=True, nullable=False, index=True)
    source_id = Column(String, ForeignKey("sources.source_id"), nullable=False, index=True)
    source_type = Column(String, nullable=False)

    event_category = Column(String, nullable=False, index=True)
    event_subcategory = Column(String, nullable=True)

    timestamp = Column(DateTime, nullable=False, index=True)
    ingestion_timestamp = Column(DateTime, nullable=False, default=utcnow)

    text = Column(Text, nullable=True)
    language = Column(String, default="en")

    city = Column(String, nullable=True, index=True)
    district = Column(String, nullable=True, index=True)
    state = Column(String, nullable=True, index=True)
    country = Column(String, default="India")

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(Geometry("POINT", srid=4326), nullable=True)

    hashtags = Column(ARRAY(String), default=[])

    image_urls = Column(ARRAY(String), default=[])
    video_urls = Column(ARRAY(String), default=[])

    source_url = Column(String, nullable=True)
    author_id_hash = Column(String, nullable=True)

    raw_payload_reference = Column(String, nullable=True)
    is_simulated = Column(Boolean, default=False)
    schema_version = Column(String, default="1.0")

    h3_index = Column(String, nullable=True, index=True)
    h3_resolution = Column(Integer, nullable=True)

    temperature_celsius = Column(Float, nullable=True)
    humidity_percent = Column(Float, nullable=True)
    rainfall_mm = Column(Float, nullable=True)
    wind_speed_kmh = Column(Float, nullable=True)
    wind_direction = Column(String, nullable=True)
    pressure_hpa = Column(Float, nullable=True)
    visibility_km = Column(Float, nullable=True)

    severity = Column(Integer, nullable=True)

    quality_status = Column(String, default="pending", index=True)
    quality_notes = Column(JSONB, default=[])

    content_hash = Column(String, nullable=True, index=True)
    embedding = Column(Vector(384), nullable=True)

    extra_metadata = Column(JSONB, default=dict)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    source = relationship("Source", back_populates="reports")
    media = relationship("ReportMedia", back_populates="report")
    relationships_a = relationship("ReportRelationship", foreign_keys="ReportRelationship.report_id_a", back_populates="report_a")
    relationships_b = relationship("ReportRelationship", foreign_keys="ReportRelationship.report_id_b", back_populates="report_b")

    __table_args__ = (
        Index("idx_report_geo_time", "h3_index", "timestamp"),
        Index("idx_report_category_time", "event_category", "timestamp"),
        Index("idx_report_source_time", "source_id", "timestamp"),
        Index("idx_report_state_category", "state", "event_category"),
    )


class ReportMedia(Base):
    __tablename__ = "report_media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, index=True)
    media_type = Column(String, nullable=False)  # image, video
    url = Column(String, nullable=False)
    storage_path = Column(String, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)
    checksum = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    report = relationship("Report", back_populates="media")


class ReportRelationship(Base):
    __tablename__ = "report_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id_a = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, index=True)
    report_id_b = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, index=True)
    relationship_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    metadata_json = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=utcnow)

    report_a = relationship("Report", foreign_keys=[report_id_a], back_populates="relationships_a")
    report_b = relationship("Report", foreign_keys=[report_id_b], back_populates="relationships_b")

    __table_args__ = (
        UniqueConstraint("report_id_a", "report_id_b", "relationship_type", name="uq_report_relationship"),
    )


class WeatherEvent(Base):
    __tablename__ = "weather_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String, unique=True, nullable=False, index=True)
    event_category = Column(String, nullable=False, index=True)
    status = Column(String, default="candidate", index=True)

    time_range_start = Column(DateTime, nullable=True)
    time_range_end = Column(DateTime, nullable=True)

    center_latitude = Column(Float, nullable=True)
    center_longitude = Column(Float, nullable=True)
    center_location = Column(Geometry("POINT", srid=4326), nullable=True)

    affected_area = Column(Geometry("POLYGON", srid=4326), nullable=True)

    source_count = Column(Integer, default=0)
    report_count = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)

    h3_cells = Column(ARRAY(String), default=[])

    severity = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)

    extra_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    event_reports = relationship("EventReport", back_populates="event")


class EventReport(Base):
    __tablename__ = "event_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("weather_events.id"), nullable=False, index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, index=True)
    attached_at = Column(DateTime, default=utcnow)
    role = Column(String, default="supporting")  # supporting, primary, duplicate

    event = relationship("WeatherEvent", back_populates="event_reports")


class EventCell(Base):
    __tablename__ = "event_cells"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("weather_events.id"), nullable=False, index=True)
    h3_index = Column(String, nullable=False, index=True)
    h3_resolution = Column(Integer, nullable=False)
    report_count = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("event_id", "h3_index", name="uq_event_cell"),
    )


class DataQuality(Base):
    __tablename__ = "data_quality"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_timestamp = Column(DateTime, default=utcnow)
    total_records = Column(Integer, default=0)
    valid_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    invalid_count = Column(Integer, default=0)
    quarantined_count = Column(Integer, default=0)
    missing_fields = Column(JSONB, default={})
    source_quality = Column(JSONB, default={})
    duplicate_candidates = Column(Integer, default=0)
    duration_ms = Column(Float, default=0.0)
    extra_metadata = Column(JSONB, default={})


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(String, unique=True, nullable=False, index=True)
    source_id = Column(String, nullable=False, index=True)
    status = Column(String, default="running")
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    records_received = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    records_quarantined = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    extra_metadata = Column(JSONB, default={})
