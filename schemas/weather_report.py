from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import orjson
from pydantic import BaseModel, Field, field_validator, model_validator


class EventCategory(str, Enum):
    RAINFALL = "rainfall"
    THUNDERSTORM = "thunderstorm"
    FLOOD = "flood"
    HEATWAVE = "heatwave"
    FOG = "fog"
    DUST_STORM = "dust_storm"
    STRONG_WIND = "strong_wind"
    LIGHTNING = "lightning"
    HAIL = "hail"
    COLD_WAVE = "cold_wave"
    OTHER = "other"


class QualityStatus(str, Enum):
    PENDING = "pending"
    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"
    QUARANTINED = "quarantined"


class SourceType(str, Enum):
    API = "api"
    DATASET = "dataset"
    WEB = "web"
    SOCIAL = "social"
    CITIZEN = "citizen"
    REPLAY = "replay"
    GENERATOR = "generator"


class WeatherReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    source_type: SourceType

    event_category: EventCategory = EventCategory.OTHER
    event_subcategory: Optional[str] = None

    timestamp: datetime
    ingestion_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    text: Optional[str] = None
    language: str = "en"

    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    hashtags: list[str] = Field(default_factory=list)

    image_urls: list[str] = Field(default_factory=list)
    video_urls: list[str] = Field(default_factory=list)

    source_url: Optional[str] = None

    author_id_hash: Optional[str] = None

    raw_payload_reference: Optional[str] = None

    is_simulated: bool = False

    schema_version: str = "1.0"

    h3_index: Optional[str] = None
    h3_resolution: Optional[int] = None

    temperature_celsius: Optional[float] = None
    humidity_percent: Optional[float] = None
    rainfall_mm: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_direction: Optional[str] = None
    pressure_hpa: Optional[float] = None
    visibility_km: Optional[float] = None

    severity: Optional[int] = Field(None, ge=1, le=10)

    quality_status: QualityStatus = QualityStatus.PENDING
    quality_notes: list[str] = Field(default_factory=list)

    content_hash: Optional[str] = None

    extra_metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    @field_validator("hashtags", mode="before")
    @classmethod
    def normalize_hashtags(cls, v: list[str]) -> list[str]:
        return [h.strip().lower() if h.startswith("#") else f"#{h.strip().lower()}" for h in v if h.strip()]

    @field_validator("text", mode="before")
    @classmethod
    def clean_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            import re
            v = v.strip()
            v = re.sub(r'\s+', ' ', v)
            if not v:
                return None
        return v

    @field_validator("city", "district", "state", mode="before")
    @classmethod
    def normalize_location_field(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().title()
            if not v:
                return None
        return v

    @model_validator(mode="after")
    def validate_coordinates(self) -> "WeatherReport":
        if self.latitude is not None and self.longitude is not None:
            if not (-90 <= self.latitude <= 90):
                raise ValueError(f"Invalid latitude: {self.latitude}")
            if not (-180 <= self.longitude <= 180):
                raise ValueError(f"Invalid longitude: {self.longitude}")
        return self

    @model_validator(mode="after")
    def compute_content_hash(self) -> "WeatherReport":
        if self.content_hash is None:
            self.content_hash = self._compute_hash()
        return self

    def _compute_hash(self) -> str:
        hash_data = {
            "source_id": self.source_id,
            "text": self.text,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "event_category": self.event_category.value,
        }
        raw = orjson.dumps(hash_data, option=orjson.OPT_SORT_KEYS).decode()
        return hashlib.sha256(raw.encode()).hexdigest()

    def to_redpanda_key(self) -> str:
        return f"{self.source_id}:{self.event_category.value}"

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class WeatherReportCreate(BaseModel):
    source_id: str
    source_type: SourceType
    event_category: EventCategory = EventCategory.OTHER
    event_subcategory: Optional[str] = None
    timestamp: Optional[datetime] = None
    text: Optional[str] = None
    language: str = "en"
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    hashtags: list[str] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
    video_urls: list[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    temperature_celsius: Optional[float] = None
    humidity_percent: Optional[float] = None
    rainfall_mm: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    severity: Optional[int] = Field(None, ge=1, le=10)
    is_simulated: bool = False
    extra_metadata: dict[str, Any] = Field(default_factory=dict)


class DuplicateRelationship(BaseModel):
    relationship_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_id_a: str
    report_id_b: str
    relationship_type: str  # exact_duplicate, near_duplicate, semantic_duplicate, media_duplicate, geo_temporal_duplicate
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventCandidate(BaseModel):
    candidate_event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_ids: list[str] = Field(default_factory=list)
    h3_cells: list[str] = Field(default_factory=list)
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    event_category: EventCategory = EventCategory.OTHER
    source_count: int = 0
    report_count: int = 0
    avg_latitude: Optional[float] = None
    avg_longitude: Optional[float] = None
    confidence_score: float = 0.0
    status: str = "candidate"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
