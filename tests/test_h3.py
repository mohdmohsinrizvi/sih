import pytest
from datetime import datetime, timezone
from schemas.weather_report import WeatherReport, EventCategory
from data_engine.h3.indexer import H3Indexer


class TestH3Indexer:
    def setup_method(self):
        self.indexer = H3Indexer()

    def test_index_report(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            latitude=26.8467,
            longitude=80.9462,
        )
        result = self.indexer.index(report)
        assert result.h3_index is not None
        assert result.h3_resolution == 7

    def test_index_custom_resolution(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            latitude=26.8467,
            longitude=80.9462,
        )
        result = self.indexer.index(report, resolution=9)
        assert result.h3_resolution == 9

    def test_index_no_coordinates(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
        )
        result = self.indexer.index(report)
        assert result.h3_index is None

    def test_get_h3_cell(self):
        cell = self.indexer.get_h3_cell(26.8467, 80.9462)
        assert cell is not None
        assert isinstance(cell, str)

    def test_get_neighbors(self):
        cell = self.indexer.get_h3_cell(26.8467, 80.9462)
        neighbors = self.indexer.get_neighbors(cell, k=1)
        assert len(neighbors) > 0
        assert cell in neighbors

    def test_get_time_bucket(self):
        ts = datetime.now(timezone.utc)
        bucket = self.indexer.get_time_bucket(ts, bucket_minutes=5)
        assert isinstance(bucket, str)

    def test_candidate_partition(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            latitude=26.8467,
            longitude=80.9462,
            event_category=EventCategory.RAINFALL,
        )
        report = self.indexer.index(report)
        partition = self.indexer.get_candidate_partition(report)
        assert partition is not None
        assert "rainfall" in partition
