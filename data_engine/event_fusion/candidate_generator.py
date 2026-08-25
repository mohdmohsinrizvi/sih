from __future__ import annotations

from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

import structlog

from schemas.weather_report import WeatherReport, EventCandidate, EventCategory

logger = structlog.get_logger(__name__)


class EventCandidateGenerator:
    def __init__(
        self,
        candidate_window_minutes: int = 60,
        min_source_count: int = 3,
        min_report_count: int = 5,
    ):
        self.window = timedelta(minutes=candidate_window_minutes)
        self.min_sources = min_source_count
        self.min_reports = min_report_count

    def generate_candidates(
        self,
        reports: list[WeatherReport],
    ) -> list[EventCandidate]:
        h3_groups: dict[str, list[WeatherReport]] = defaultdict(list)
        for report in reports:
            if report.h3_index:
                key = f"{report.h3_index}:{report.event_category.value}"
                h3_groups[key].append(report)

        category_groups: dict[EventCategory, list[WeatherReport]] = defaultdict(list)
        for report in reports:
            category_groups[report.event_category].append(report)

        candidates = []

        for group_key, group_reports in h3_groups.items():
            candidate = self._build_candidate(group_reports)
            if candidate:
                candidates.append(candidate)

        for category, cat_reports in category_groups.items():
            time_sorted = sorted(cat_reports, key=lambda r: r.timestamp)
            clusters = self._temporal_cluster(time_sorted)
            for cluster in clusters:
                candidate = self._build_candidate(cluster)
                if candidate:
                    candidates.append(candidate)

        merged = self._merge_overlapping_candidates(candidates)

        logger.info(
            "event_candidates_generated",
            total_reports=len(reports),
            candidates=len(merged),
        )

        return merged

    def _build_candidate(self, reports: list[WeatherReport]) -> Optional[EventCandidate]:
        if len(reports) < self.min_reports:
            return None

        sources = set(r.source_id for r in reports)
        if len(sources) < self.min_sources:
            return None

        timestamps = [r.timestamp for r in reports if r.timestamp]
        h3_cells = list(set(r.h3_index for r in reports if r.h3_index))

        lats = [r.latitude for r in reports if r.latitude is not None]
        lons = [r.longitude for r in reports if r.longitude is not None]

        category = reports[0].event_category

        confidence = 0.0
        if len(sources) >= 5:
            confidence += 0.3
        elif len(sources) >= 3:
            confidence += 0.2

        if len(reports) >= 20:
            confidence += 0.3
        elif len(reports) >= 10:
            confidence += 0.2
        elif len(reports) >= 5:
            confidence += 0.1

        if len(h3_cells) >= 3:
            confidence += 0.2

        severity_reports = [r for r in reports if r.severity is not None]
        if severity_reports:
            avg_severity = sum(r.severity for r in severity_reports) / len(severity_reports)
            if avg_severity >= 7:
                confidence += 0.2

        return EventCandidate(
            report_ids=[r.report_id for r in reports],
            h3_cells=h3_cells,
            time_range_start=min(timestamps) if timestamps else None,
            time_range_end=max(timestamps) if timestamps else None,
            event_category=category,
            source_count=len(sources),
            report_count=len(reports),
            avg_latitude=sum(lats) / len(lats) if lats else None,
            avg_longitude=sum(lons) / len(lons) if lons else None,
            confidence_score=min(confidence, 1.0),
        )

    def _temporal_cluster(self, reports: list[WeatherReport]) -> list[list[WeatherReport]]:
        if not reports:
            return []

        clusters = []
        current_cluster = [reports[0]]

        for i in range(1, len(reports)):
            if (reports[i].timestamp - current_cluster[-1].timestamp) <= self.window:
                current_cluster.append(reports[i])
            else:
                if current_cluster:
                    clusters.append(current_cluster)
                current_cluster = [reports[i]]

        if current_cluster:
            clusters.append(current_cluster)

        return [c for c in clusters if len(c) >= self.min_reports]

    def _merge_overlapping_candidates(
        self,
        candidates: list[EventCandidate],
    ) -> list[EventCandidate]:
        if not candidates:
            return []

        sorted_candidates = sorted(candidates, key=lambda c: c.confidence_score, reverse=True)
        merged = []
        seen_reports: set[str] = set()

        for candidate in sorted_candidates:
            overlap = len(set(candidate.report_ids) & seen_reports)
            if overlap > len(candidate.report_ids) * 0.5:
                continue

            merged.append(candidate)
            seen_reports.update(candidate.report_ids)

        return merged


generator = EventCandidateGenerator()
