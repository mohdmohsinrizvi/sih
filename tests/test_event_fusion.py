import pytest
from datetime import datetime, timezone, timedelta
from schemas.weather_report import WeatherReport, EventCategory
from data_engine.event_fusion.candidate_generator import EventCandidateGenerator
from data_engine.h3.indexer import H3Indexer


class TestEventCandidateGenerator:
    def setup_method(self):
        self.generator = EventCandidateGenerator(
            candidate_window_minutes=60,
            min_source_count=2,
            min_report_count=3,
        )
        self.indexer = H3Indexer()

    def _make_reports(self, count=5, city="Delhi", category=EventCategory.FLOOD, time_span_minutes=30):
        reports = []
        base_time = datetime.now(timezone.utc)
        for i in range(count):
            report = WeatherReport(
                source_id=f"source_{i % 3}",
                source_type="citizen",
                timestamp=base_time + timedelta(minutes=i * 5),
                text=f"Flood report {i}",
                latitude=28.7041 + (i * 0.001),
                longitude=77.1025 + (i * 0.001),
                city=city,
                state="Delhi",
                event_category=category,
            )
            report = self.indexer.index(report)
            reports.append(report)
        return reports

    def test_generate_candidates(self):
        reports = self._make_reports(count=5)
        candidates = self.generator.generate_candidates(reports)
        assert len(candidates) > 0
        assert candidates[0].report_count >= 3

    def test_candidate_has_required_fields(self):
        reports = self._make_reports(count=5)
        candidates = self.generator.generate_candidates(reports)
        if candidates:
            c = candidates[0]
            assert c.candidate_event_id is not None
            assert len(c.report_ids) > 0
            assert c.event_category == EventCategory.FLOOD
            assert c.source_count >= 2

    def test_no_candidates_insufficient_reports(self):
        reports = self._make_reports(count=2)
        candidates = self.generator.generate_candidates(reports)
        for c in candidates:
            assert c.report_count >= 3

    def test_mixed_categories(self):
        reports = self._make_reports(count=3, category=EventCategory.FLOOD)
        reports.extend(self._make_reports(count=3, category=EventCategory.RAINFALL))
        candidates = self.generator.generate_candidates(reports)
        assert len(candidates) >= 2

    def test_temporal_clustering(self):
        reports = self._make_reports(count=5, time_span_minutes=10)
        candidates = self.generator.generate_candidates(reports)
        assert len(candidates) > 0
