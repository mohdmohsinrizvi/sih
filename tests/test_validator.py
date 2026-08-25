import pytest
from datetime import datetime, timezone, timedelta
from schemas.weather_report import WeatherReport, EventCategory, QualityStatus
from data_engine.quality.validator import DataQualityValidator


class TestDataQualityValidator:
    def setup_method(self):
        self.validator = DataQualityValidator()

    def test_valid_report(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            text="Heavy rain in Delhi",
            latitude=28.7041,
            longitude=77.1025,
            city="Delhi",
            state="Delhi",
            event_category=EventCategory.RAINFALL,
        )
        result = self.validator.validate(report)
        assert result.quality_status == QualityStatus.VALID

    def test_warning_future_timestamp(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc) + timedelta(hours=5),
            text="test",
        )
        result = self.validator.validate(report)
        assert result.quality_status == QualityStatus.WARNING
        assert any("future" in n.lower() for n in result.quality_notes)

    def test_warning_old_timestamp(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime(2000, 1, 1, tzinfo=timezone.utc),
            text="test",
        )
        result = self.validator.validate(report)
        assert result.quality_status == QualityStatus.WARNING

    def test_warning_outside_india_bounds(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            text="test",
            latitude=50.0,
            longitude=80.0,
        )
        result = self.validator.validate(report)
        assert result.quality_status == QualityStatus.WARNING

    def test_invalid_no_source(self):
        report = WeatherReport(
            source_id="",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
        )
        result = self.validator.validate(report)
        assert result.quality_status == QualityStatus.INVALID

    def test_warning_impossible_temperature(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            temperature_celsius=100,
        )
        result = self.validator.validate(report)
        assert result.quality_status == QualityStatus.WARNING

    def test_warning_impossible_humidity(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            humidity_percent=150,
        )
        result = self.validator.validate(report)
        assert result.quality_status == QualityStatus.WARNING

    def test_warning_negative_rainfall(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
            rainfall_mm=-5,
        )
        result = self.validator.validate(report)
        assert result.quality_status == QualityStatus.WARNING

    def test_warning_no_content(self):
        report = WeatherReport(
            source_id="test",
            source_type="api",
            timestamp=datetime.now(timezone.utc),
        )
        result = self.validator.validate(report)
        assert result.quality_status == QualityStatus.WARNING
