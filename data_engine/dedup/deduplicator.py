from __future__ import annotations

import hashlib
import math
from typing import Optional
from datetime import datetime, timedelta

import structlog

from schemas.weather_report import WeatherReport, DuplicateRelationship

logger = structlog.get_logger(__name__)


class Deduplicator:
    def __init__(
        self,
        text_similarity_threshold: float = 0.6,
        geo_distance_meters: float = 1000,
        time_window_minutes: int = 30,
    ):
        self.text_threshold = text_similarity_threshold
        self.geo_distance = geo_distance_meters
        self.time_window = timedelta(minutes=time_window_minutes)
        self._seen_content_hashes: dict[str, str] = {}
        self._candidate_cache: dict[str, list[str]] = {}

    def check_exact_duplicate(self, report: WeatherReport) -> Optional[str]:
        if report.content_hash in self._seen_content_hashes:
            existing_id = self._seen_content_hashes[report.content_hash]
            logger.info(
                "exact_duplicate_found",
                report_id=report.report_id,
                duplicate_of=existing_id,
            )
            return existing_id
        self._seen_content_hashes[report.content_hash] = report.report_id
        return None

    def check_near_duplicate(
        self,
        report: WeatherReport,
        candidate_reports: list[WeatherReport],
    ) -> list[DuplicateRelationship]:
        relationships = []
        for candidate in candidate_reports:
            if candidate.report_id == report.report_id:
                continue

            text_sim = self._text_similarity(report.text, candidate.text)
            if text_sim < self.text_threshold:
                continue

            geo_match = self._geo_match(report, candidate)
            time_match = self._time_match(report, candidate)
            category_match = report.event_category == candidate.event_category

            confidence = 0.0
            if text_sim > 0.9:
                confidence += 0.4
            elif text_sim > 0.7:
                confidence += 0.2

            if geo_match:
                confidence += 0.3
            if time_match:
                confidence += 0.2
            if category_match:
                confidence += 0.1

            if confidence >= 0.5:
                rel_type = "near_duplicate" if confidence < 0.8 else "semantic_duplicate"
                relationships.append(DuplicateRelationship(
                    report_id_a=report.report_id,
                    report_id_b=candidate.report_id,
                    relationship_type=rel_type,
                    confidence=min(confidence, 1.0),
                    metadata={
                        "text_similarity": text_sim,
                        "geo_match": geo_match,
                        "time_match": time_match,
                        "category_match": category_match,
                    },
                ))

        return relationships

    def check_geo_temporal_duplicate(
        self,
        report: WeatherReport,
        candidate_reports: list[WeatherReport],
    ) -> list[DuplicateRelationship]:
        relationships = []
        for candidate in candidate_reports:
            if candidate.report_id == report.report_id:
                continue

            if report.event_category != candidate.event_category:
                continue

            distance = self._haversine_distance(
                report.latitude, report.longitude,
                candidate.latitude, candidate.longitude,
            )
            if distance is None or distance > self.geo_distance:
                continue

            time_diff = abs((report.timestamp - candidate.timestamp).total_seconds())
            if time_diff > self.time_window.total_seconds():
                continue

            confidence = 0.7
            if distance < 100:
                confidence += 0.15
            if time_diff < 300:
                confidence += 0.15

            relationships.append(DuplicateRelationship(
                report_id_a=report.report_id,
                report_id_b=candidate.report_id,
                relationship_type="geo_temporal_duplicate",
                confidence=min(confidence, 1.0),
                metadata={
                    "distance_meters": distance,
                    "time_diff_seconds": time_diff,
                },
            ))

        return relationships

    def generate_candidates(
        self,
        reports: list[WeatherReport],
    ) -> list[DuplicateRelationship]:
        all_relationships = []

        seen_hashes = {}
        for report in reports:
            if report.content_hash in seen_hashes:
                all_relationships.append(DuplicateRelationship(
                    report_id_a=report.report_id,
                    report_id_b=seen_hashes[report.content_hash],
                    relationship_type="exact_duplicate",
                    confidence=1.0,
                ))
            else:
                seen_hashes[report.content_hash] = report.report_id

        h3_buckets: dict[str, list[WeatherReport]] = {}
        for report in reports:
            if report.h3_index:
                bucket_key = f"{report.h3_index}:{report.event_category.value}"
                if bucket_key not in h3_buckets:
                    h3_buckets[bucket_key] = []
                h3_buckets[bucket_key].append(report)

        for bucket_key, bucket_reports in h3_buckets.items():
            if len(bucket_reports) > 1:
                for i, report in enumerate(bucket_reports):
                    candidates = bucket_reports[i+1:i+20]
                    near_dups = self.check_near_duplicate(report, candidates)
                    all_relationships.extend(near_dups)

                    geo_dups = self.check_geo_temporal_duplicate(report, candidates)
                    all_relationships.extend(geo_dups)

        logger.info(
            "dedup_candidates_generated",
            total_reports=len(reports),
            total_relationships=len(all_relationships),
        )

        return all_relationships

    def _text_similarity(self, text_a: Optional[str], text_b: Optional[str]) -> float:
        if not text_a or not text_b:
            return 0.0

        tokens_a = set(text_a.lower().split())
        tokens_b = set(text_b.lower().split())

        if not tokens_a or not tokens_b:
            return 0.0

        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b

        return len(intersection) / len(union) if union else 0.0

    def _geo_match(self, a: WeatherReport, b: WeatherReport) -> bool:
        if a.latitude is None or b.latitude is None:
            return False
        if a.longitude is None or b.longitude is None:
            return False

        distance = self._haversine_distance(a.latitude, a.longitude, b.latitude, b.longitude)
        return distance is not None and distance <= self.geo_distance

    def _time_match(self, a: WeatherReport, b: WeatherReport) -> bool:
        if a.timestamp is None or b.timestamp is None:
            return False
        return abs((a.timestamp - b.timestamp).total_seconds()) <= self.time_window.total_seconds()

    def _haversine_distance(
        self,
        lat1: Optional[float], lon1: Optional[float],
        lat2: Optional[float], lon2: Optional[float],
    ) -> Optional[float]:
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return None

        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c


deduplicator = Deduplicator()
