from __future__ import annotations

from typing import Optional

import h3
import structlog

from schemas.weather_report import WeatherReport

logger = structlog.get_logger(__name__)

DEFAULT_RESOLUTION = 7
SUPPORTED_RESOLUTIONS = [5, 6, 7, 8, 9]


class H3Indexer:
    def __init__(self, default_resolution: int = DEFAULT_RESOLUTION):
        self.default_resolution = default_resolution

    def index(self, report: WeatherReport, resolution: Optional[int] = None) -> WeatherReport:
        if report.latitude is None or report.longitude is None:
            return report

        res = resolution or self.default_resolution

        try:
            h3_cell = h3.latlng_to_cell(report.latitude, report.longitude, res)
            report.h3_index = h3_cell
            report.h3_resolution = res
        except Exception as e:
            logger.warning(
                "h3_indexing_failed",
                report_id=report.report_id,
                lat=report.latitude,
                lon=report.longitude,
                error=str(e),
            )

        return report

    def get_h3_cell(self, lat: float, lon: float, resolution: int = DEFAULT_RESOLUTION) -> Optional[str]:
        try:
            return h3.latlng_to_cell(lat, lon, resolution)
        except Exception:
            return None

    def get_neighbors(self, h3_cell: str, k: int = 1) -> set[str]:
        try:
            return h3.grid_disk(h3_cell, k)
        except Exception:
            return set()

    def get_distance(self, cell_a: str, cell_b: str) -> Optional[int]:
        try:
            return h3.grid_distance(cell_a, cell_b)
        except Exception:
            return None

    def get_time_bucket(self, timestamp, bucket_minutes: int = 5) -> str:
        if hasattr(timestamp, "timestamp"):
            ts = timestamp.timestamp()
        else:
            ts = float(timestamp)
        bucket_seconds = bucket_minutes * 60
        bucket_id = int(ts // bucket_seconds)
        return str(bucket_id)

    def get_candidate_partition(
        self,
        report: WeatherReport,
        time_bucket_minutes: int = 5,
    ) -> Optional[str]:
        if report.h3_index is None:
            return None
        bucket = self.get_time_bucket(report.timestamp, time_bucket_minutes)
        return f"{report.h3_index}:{bucket}:{report.event_category.value}"

    def compute_cell_distance(self, cell_a: str, cell_b: str, resolution: int = DEFAULT_RESOLUTION) -> Optional[float]:
        try:
            boundary_a = h3.cell_to_boundary(cell_a)
            boundary_b = h3.cell_to_boundary(cell_b)

            lat_a = sum(p[0] for p in boundary_a) / len(boundary_a)
            lon_a = sum(p[1] for p in boundary_a) / len(boundary_a)
            lat_b = sum(p[0] for p in boundary_b) / len(boundary_b)
            lon_b = sum(p[1] for p in boundary_b) / len(boundary_b)

            import math
            dlat = math.radians(lat_b - lat_a)
            dlon = math.radians(lon_b - lon_a)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat_a)) * math.cos(math.radians(lat_b)) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            km = 6371 * c
            return km * 1000
        except Exception:
            return None


indexer = H3Indexer()
