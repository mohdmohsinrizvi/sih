import pytest
from datetime import datetime, timezone, timedelta
from schemas.weather_report import WeatherReport, EventCategory
from data_engine.dedup.deduplicator import Deduplicator


class TestDeduplicator:
    def setup_method(self):
        self.deduplicator = Deduplicator()

    def test_exact_duplicate(self):
        report_a = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            text="Heavy rain in Delhi",
            latitude=28.7041,
            longitude=77.1025,
            event_category=EventCategory.RAINFALL,
        )
        report_b = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            text="Heavy rain in Delhi",
            latitude=28.7041,
            longitude=77.1025,
            event_category=EventCategory.RAINFALL,
        )

        dup_id = self.deduplicator.check_exact_duplicate(report_a)
        assert dup_id is None

        dup_id = self.deduplicator.check_exact_duplicate(report_a)
        assert dup_id == report_a.report_id

    def test_near_duplicate(self):
        report_a = WeatherReport(
            source_id="test_a",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            text="Heavy rainfall reported in Lucknow area, streets flooded",
            latitude=26.8467,
            longitude=80.9462,
            event_category=EventCategory.RAINFALL,
        )
        report_b = WeatherReport(
            source_id="test_b",
            source_type="citizen",
            timestamp=datetime.now(timezone.utc) + timedelta(minutes=5),
            text="Heavy rainfall reported in Lucknow city, streets flooded",
            latitude=26.85,
            longitude=80.95,
            event_category=EventCategory.RAINFALL,
        )

        relationships = self.deduplicator.check_near_duplicate(report_a, [report_b])
        assert len(relationships) > 0
        assert relationships[0].confidence > 0.5

    def test_geo_temporal_duplicate(self):
        report_a = WeatherReport(
            source_id="test_a",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            text="Flood in Guwahati",
            latitude=26.1445,
            longitude=91.7362,
            event_category=EventCategory.FLOOD,
        )
        report_b = WeatherReport(
            source_id="test_b",
            source_type="citizen",
            timestamp=datetime.now(timezone.utc) + timedelta(minutes=10),
            text="Flood situation worsening in Guwahati",
            latitude=26.15,
            longitude=91.74,
            event_category=EventCategory.FLOOD,
        )

        relationships = self.deduplicator.check_geo_temporal_duplicate(report_a, [report_b])
        assert len(relationships) > 0
        assert relationships[0].relationship_type == "geo_temporal_duplicate"

    def test_generate_candidates(self):
        reports = [
            WeatherReport(
                source_id="test",
                source_type="api",
                timestamp=datetime.now(timezone.utc),
                text="Rain in Delhi",
                latitude=28.7041,
                longitude=77.1025,
                event_category=EventCategory.RAINFALL,
                h3_index="87283472bffffff",
            )
            for _ in range(5)
        ]

        relationships = self.deduplicator.generate_candidates(reports)
        assert len(relationships) > 0

    def test_no_duplicate_different_category(self):
        report_a = WeatherReport(
            source_id="test_a",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            text="Rain in Delhi",
            latitude=28.7041,
            longitude=77.1025,
            event_category=EventCategory.RAINFALL,
        )
        report_b = WeatherReport(
            source_id="test_b",
            source_type="citizen",
            timestamp=datetime.now(timezone.utc) + timedelta(minutes=5),
            text="Heatwave in Delhi",
            latitude=28.71,
            longitude=77.11,
            event_category=EventCategory.HEATWAVE,
        )

        relationships = self.deduplicator.check_geo_temporal_duplicate(report_a, [report_b])
        assert len(relationships) == 0
