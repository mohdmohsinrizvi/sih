from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

import structlog

from schemas.weather_report import WeatherReport, QualityStatus

logger = structlog.get_logger(__name__)

INDIA_BOUNDS = {
    "lat_min": 6.0,
    "lat_max": 37.6,
    "lon_min": 68.0,
    "lon_max": 97.5,
}

FUTURE_MAX_HOURS = 2
OLD_MAX_DAYS = 3650


class DataQualityValidator:
    def validate(self, report: WeatherReport) -> WeatherReport:
        notes = []
        status = QualityStatus.VALID

        if report.timestamp:
            now = datetime.now(timezone.utc)
            diff = now - report.timestamp
            if diff.total_seconds() < -FUTURE_MAX_HOURS * 3600:
                notes.append(f"Timestamp is in the future by {abs(diff.total_seconds()/3600):.1f} hours")
                status = QualityStatus.WARNING
            elif diff.total_seconds() > OLD_MAX_DAYS * 86400:
                notes.append(f"Timestamp is {diff.days} days old")
                status = QualityStatus.WARNING

        if report.latitude is not None and report.longitude is not None:
            if not (INDIA_BOUNDS["lat_min"] <= report.latitude <= INDIA_BOUNDS["lat_max"]):
                notes.append(f"Latitude {report.latitude} outside India bounds")
                status = QualityStatus.WARNING
            if not (INDIA_BOUNDS["lon_min"] <= report.longitude <= INDIA_BOUNDS["lon_max"]):
                notes.append(f"Longitude {report.longitude} outside India bounds")
                status = QualityStatus.WARNING

        if not report.source_id:
            notes.append("Missing or empty source_id")
            status = QualityStatus.INVALID

        if report.text is None and not report.image_urls and not report.video_urls:
            notes.append("No text or media content")
            if status == QualityStatus.VALID:
                status = QualityStatus.WARNING

        if report.temperature_celsius is not None:
            if not (-60 <= report.temperature_celsius <= 60):
                notes.append(f"Impossible temperature: {report.temperature_celsius}°C")
                status = QualityStatus.WARNING

        if report.humidity_percent is not None:
            if not (0 <= report.humidity_percent <= 100):
                notes.append(f"Impossible humidity: {report.humidity_percent}%")
                status = QualityStatus.WARNING

        if report.rainfall_mm is not None:
            if report.rainfall_mm < 0:
                notes.append(f"Negative rainfall: {report.rainfall_mm}")
                status = QualityStatus.WARNING

        if report.wind_speed_kmh is not None:
            if report.wind_speed_kmh < 0 or report.wind_speed_kmh > 500:
                notes.append(f"Impossible wind speed: {report.wind_speed_kmh}")
                status = QualityStatus.WARNING

        if report.severity is not None:
            if not (1 <= report.severity <= 10):
                notes.append(f"Invalid severity: {report.severity}")
                status = QualityStatus.WARNING

        report.quality_status = status
        report.quality_notes = notes

        if status == QualityStatus.INVALID:
            logger.warning(
                "record_invalid",
                report_id=report.report_id,
                source_id=report.source_id,
                notes=notes,
            )

        return report


validator = DataQualityValidator()
