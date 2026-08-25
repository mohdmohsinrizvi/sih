from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

import structlog

from schemas.weather_report import (
    WeatherReport,
    WeatherReportCreate,
    EventCategory,
    SourceType,
)
from connectors.base import RawPayload

logger = structlog.get_logger(__name__)

INDIAN_STATES = {
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
    "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu",
    "telangana", "tripura", "uttar pradesh", "uttarakhand", "west bengal",
    "andaman and nicobar islands", "chandigarh", "dadra and nagar haveli",
    "daman and diu", "delhi", "jammu and kashmir", "ladakh", "lakshadweep",
    "puducherry",
}

EVENT_KEYWORDS = {
    EventCategory.RAINFALL: ["rain", "rainfall", "precipitation", "drizzle", "shower", "downpour", "wet"],
    EventCategory.THUNDERSTORM: ["thunder", "thunderstorm", "lightning storm", "tempest"],
    EventCategory.FLOOD: ["flood", "flooding", "deluge", "inundation", "submerged", "waterlogging"],
    EventCategory.HEATWAVE: ["heatwave", "heat wave", "scorching", "extreme heat", "hot", "temperature"],
    EventCategory.FOG: ["fog", "mist", "haze", "low visibility", "smog"],
    EventCategory.DUST_STORM: ["dust storm", "sandstorm", "dust", "sand", "visibility reduced"],
    EventCategory.STRONG_WIND: ["wind", "gale", "storm", "cyclone", "gusty", "strong wind"],
    EventCategory.LIGHTNING: ["lightning", "thunderbolt", "lightning strike"],
    EventCategory.HAIL: ["hail", "hailstone", "ice pellet"],
    EventCategory.COLD_WAVE: ["cold wave", "frost", "freeze", "chilling", "cold"],
}

SEVERITY_KEYWORDS = {
    10: ["catastrophic", "devastating", "massive destruction"],
    9: ["severe", "extreme", "dangerous", "emergency"],
    8: ["very heavy", "extreme", "intense"],
    7: ["heavy", "significant", "major"],
    6: ["moderate to heavy", "notable"],
    5: ["moderate", "steady"],
    4: ["light to moderate"],
    3: ["light", "mild"],
    2: ["very light", "trace"],
    1: ["barely", "negligible"],
}

HASHTAG_NORMALIZATION = {
    "#rain": "#rainfall",
    "#raining": "#rainfall",
    "#storm": "#thunderstorm",
    "#flooding": "#flood",
    "#flooded": "#flood",
    "#hot": "#heatwave",
    "#heat": "#heatwave",
    "#windy": "#strong_wind",
    "#icy": "#cold_wave",
}


class Normalizer:
    def normalize(self, payload: RawPayload) -> Optional[WeatherReport]:
        try:
            content = payload.content
            if not isinstance(content, dict):
                logger.warning("non_dict_content", source_id=payload.source_id)
                return None

            report_data = self._extract_fields(payload)

            if report_data.get("timestamp"):
                report_data["timestamp"] = self._normalize_timestamp(report_data["timestamp"])
            else:
                report_data["timestamp"] = datetime.now(timezone.utc)

            report_data["latitude"], report_data["longitude"] = self._normalize_gps(
                report_data.get("latitude"),
                report_data.get("longitude"),
            )

            if report_data.get("text"):
                report_data["text"] = self._clean_text(report_data["text"])

            if report_data.get("hashtags"):
                report_data["hashtags"] = self._normalize_hashtags(report_data["hashtags"])
            else:
                report_data["hashtags"] = []

            report_data["event_category"] = self._infer_event_category(
                report_data.get("text", ""),
                report_data.get("hashtags", []),
                report_data.get("event_category"),
            )

            report_data["state"] = self._normalize_state(report_data.get("state"))
            report_data["city"] = self._normalize_city(report_data.get("city"))
            report_data["district"] = self._normalize_city(report_data.get("district"))

            report_data["severity"] = self._infer_severity(
                report_data.get("text", ""),
                report_data.get("severity"),
            )

            report_data["source_id"] = payload.source_id
            report_data["source_type"] = SourceType(payload.source_type)
            report_data["raw_payload_reference"] = payload.checksum
            report_data["ingestion_timestamp"] = datetime.now(timezone.utc)
            report_data["is_simulated"] = content.get("is_simulated", False)

            optional_fields = [
                "temperature_celsius", "humidity_percent", "rainfall_mm",
                "wind_speed_kmh", "wind_direction", "pressure_hpa",
                "visibility_km", "event_subcategory", "language",
                "image_urls", "video_urls", "source_url", "author_id_hash",
                "extra_metadata",
            ]
            for field in optional_fields:
                if field not in report_data or report_data[field] is None:
                    report_data[field] = content.get(field)

            report_data = {k: v for k, v in report_data.items() if v is not None}

            return WeatherReport(**report_data)

        except Exception as e:
            logger.error(
                "normalization_failed",
                source_id=payload.source_id,
                error=str(e),
            )
            return None

    def _extract_fields(self, payload: RawPayload) -> dict:
        c = payload.content
        return {
            "report_id": c.get("report_id"),
            "text": c.get("text") or c.get("description") or c.get("content") or c.get("message"),
            "city": c.get("city") or c.get("location_city") or c.get("place"),
            "district": c.get("district") or c.get("location_district"),
            "state": c.get("state") or c.get("location_state") or c.get("region"),
            "latitude": c.get("latitude") or c.get("lat") or c.get("geo_lat"),
            "longitude": c.get("longitude") or c.get("lon") or c.get("lng") or c.get("geo_lon"),
            "hashtags": c.get("hashtags") or c.get("tags") or [],
            "event_category": c.get("event_category") or c.get("event_type"),
            "timestamp": c.get("timestamp") or c.get("date") or c.get("time") or c.get("created_at"),
            "image_urls": c.get("image_urls") or c.get("images") or [],
            "video_urls": c.get("video_urls") or c.get("videos") or [],
            "source_url": c.get("source_url") or c.get("url") or c.get("link"),
            "author_id_hash": c.get("author_id_hash") or c.get("user_id_hash"),
            "temperature_celsius": c.get("temperature_celsius") or c.get("temperature"),
            "humidity_percent": c.get("humidity_percent") or c.get("humidity"),
            "rainfall_mm": c.get("rainfall_mm") or c.get("rainfall") or c.get("precipitation"),
            "wind_speed_kmh": c.get("wind_speed_kmh") or c.get("wind_speed"),
            "severity": c.get("severity"),
            "language": c.get("language", "en"),
        }

    def _normalize_timestamp(self, ts) -> Optional[datetime]:
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                return ts.replace(tzinfo=timezone.utc)
            return ts
        if isinstance(ts, (int, float)):
            try:
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                return dt
            except (ValueError, OSError):
                return None
        if isinstance(ts, str):
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d",
                "%d/%m/%Y %H:%M:%S",
                "%d-%m-%Y %H:%M:%S",
            ]
            for fmt in formats:
                try:
                    dt = datetime.strptime(ts, fmt)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except ValueError:
                    continue
            logger.warning("unparseable_timestamp", raw=ts)
            return None
        return None

    def _normalize_gps(self, lat, lon) -> tuple[Optional[float], Optional[float]]:
        try:
            lat = float(lat) if lat is not None else None
            lon = float(lon) if lon is not None else None
        except (ValueError, TypeError):
            return None, None

        if lat is not None and not (-90 <= lat <= 90):
            logger.warning("invalid_latitude", lat=lat)
            lat = None
        if lon is not None and not (-180 <= lon <= 180):
            logger.warning("invalid_longitude", lon=lon)
            lon = None

        return lat, lon

    def _clean_text(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        return text.strip()

    def _normalize_hashtags(self, hashtags: list) -> list[str]:
        normalized = set()
        for tag in hashtags:
            if not isinstance(tag, str):
                continue
            tag = tag.strip().lower()
            if not tag.startswith("#"):
                tag = f"#{tag}"
            tag = HASHTAG_NORMALIZATION.get(tag, tag)
            normalized.add(tag)
        return sorted(normalized)

    def _infer_event_category(self, text: str, hashtags: list, declared: Optional[str]) -> EventCategory:
        if declared:
            try:
                return EventCategory(declared.lower().replace(" ", "_").replace("-", "_"))
            except ValueError:
                pass

        combined = f"{text or ''} {' '.join(hashtags or [])}".lower()

        best_category = EventCategory.OTHER
        best_score = 0

        for category, keywords in EVENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            if score > best_score:
                best_score = score
                best_category = category

        return best_category

    def _normalize_state(self, state: Optional[str]) -> Optional[str]:
        if not state:
            return None
        state = state.strip().title()
        if state.lower() in INDIAN_STATES:
            return state
        for valid_state in INDIAN_STATES:
            if valid_state in state.lower() or state.lower() in valid_state:
                return valid_state.title()
        return state

    def _normalize_city(self, city: Optional[str]) -> Optional[str]:
        if not city:
            return None
        return city.strip().title()

    def _infer_severity(self, text: Optional[str], declared: Optional[int]) -> Optional[int]:
        if declared and 1 <= declared <= 10:
            return declared

        if not text:
            return None

        text_lower = text.lower()
        for severity, keywords in SEVERITY_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    return severity
        return None


normalizer = Normalizer()
