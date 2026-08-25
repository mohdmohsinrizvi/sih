import pytest
from datetime import datetime, timezone
from schemas.weather_report import WeatherReport, EventCategory, QualityStatus, SourceType


class TestWeatherReport:
    def test_create_report(self, sample_report_data):
        report = WeatherReport(**sample_report_data)
        assert report.report_id == "test-001"
        assert report.source_id == "citizen_report"
        assert report.source_type == SourceType.CITIZEN
        assert report.event_category == EventCategory.RAINFALL
        assert report.city == "Lucknow"
        assert report.state == "Uttar Pradesh"
        assert report.latitude == 26.8467
        assert report.longitude == 80.9462
        assert report.is_simulated is True

    def test_report_generates_id(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
        )
        assert report.report_id is not None
        assert len(report.report_id) > 0

    def test_report_generates_content_hash(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            text="test report",
        )
        assert report.content_hash is not None
        assert len(report.content_hash) == 64

    def test_report_normalizes_hashtags(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            hashtags=["Rain", "  FLOOD  ", "#Thunder"],
        )
        assert "#rain" in report.hashtags
        assert "#flood" in report.hashtags
        assert "#thunder" in report.hashtags

    def test_report_validates_coordinates(self):
        with pytest.raises(ValueError):
            WeatherReport(
                source_id="test",
                source_type="api",
                timestamp=datetime.now(timezone.utc),
                latitude=100,
                longitude=80,
            )

    def test_report_normalizes_text(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            text="  Hello   World  ",
        )
        assert report.text == "Hello World"

    def test_report_default_values(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
        )
        assert report.event_category == EventCategory.OTHER
        assert report.country == "India"
        assert report.language == "en"
        assert report.schema_version == "1.0"
        assert report.quality_status == QualityStatus.PENDING

    def test_report_to_dict(self, sample_report_data):
        report = WeatherReport(**sample_report_data)
        d = report.to_dict()
        assert isinstance(d, dict)
        assert d["report_id"] == "test-001"

    def test_report_to_redpanda_key(self, sample_report_data):
        report = WeatherReport(**sample_report_data)
        key = report.to_redpanda_key()
        assert "citizen_report" in key
        assert "rainfall" in key
