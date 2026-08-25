import pytest
from datetime import datetime, timezone
from data_engine.normalization.normalizer import Normalizer
from connectors.base import RawPayload


class TestNormalizer:
    def setup_method(self):
        self.normalizer = Normalizer()

    def test_normalize_api_payload(self, sample_api_payload):
        payload = RawPayload(
            source_id="imd_api",
            source_type="api",
            content={
                "data": {"station": "Delhi", "temp": 42.5},
                "text": "Heatwave conditions reported in Delhi",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        report = self.normalizer.normalize(payload)
        assert report is not None
        assert report.source_id == "imd_api"
        assert report.text is not None

    def test_normalize_citizen_payload(self, sample_report_data):
        payload = RawPayload(
            source_id="citizen_report",
            source_type="citizen",
            content=sample_report_data,
        )
        report = self.normalizer.normalize(payload)
        assert report is not None
        assert report.city == "Lucknow"
        assert report.latitude == 26.8467

    def test_normalize_social_payload(self, sample_social_payload):
        payload = RawPayload(
            source_id="social_media",
            source_type="social",
            content=sample_social_payload,
        )
        report = self.normalizer.normalize(payload)
        assert report is not None
        assert report.hashtags

    def test_infer_event_category_from_text(self):
        payload = RawPayload(
            source_id="test",
            source_type="citizen",
            content={"text": "Severe flood in Mumbai, water everywhere"},
        )
        report = self.normalizer.normalize(payload)
        assert report is not None
        assert report.event_category.value == "flood"

    def test_infer_event_category_from_hashtags(self):
        payload = RawPayload(
            source_id="test",
            source_type="citizen",
            content={"text": "Stay safe!", "hashtags": ["#heatwave"]},
        )
        report = self.normalizer.normalize(payload)
        assert report is not None
        assert report.event_category.value == "heatwave"

    def test_normalize_timestamp_string(self):
        payload = RawPayload(
            source_id="test",
            source_type="api",
            content={"text": "test", "timestamp": "2024-01-15T10:30:00Z"},
        )
        report = self.normalizer.normalize(payload)
        assert report is not None
        assert isinstance(report.timestamp, datetime)

    def test_normalize_timestamp_epoch(self):
        payload = RawPayload(
            source_id="test",
            source_type="api",
            content={"text": "test", "timestamp": 1705312200},
        )
        report = self.normalizer.normalize(payload)
        assert report is not None

    def test_normalize_state(self):
        payload = RawPayload(
            source_id="test",
            source_type="citizen",
            content={"text": "rain", "state": "uttar pradesh"},
        )
        report = self.normalizer.normalize(payload)
        assert report is not None
        assert report.state == "Uttar Pradesh"

    def test_normalize_invalid_gps(self):
        payload = RawPayload(
            source_id="test",
            source_type="citizen",
            content={"text": "rain", "latitude": 200, "longitude": 80},
        )
        report = self.normalizer.normalize(payload)
        assert report is not None
        assert report.latitude is None

    def test_normalize_empty_content(self):
        payload = RawPayload(
            source_id="test",
            source_type="api",
            content={},
        )
        report = self.normalizer.normalize(payload)
        assert report is not None

    def test_normalize_non_dict_content(self):
        payload = RawPayload(
            source_id="test",
            source_type="api",
            content="not a dict",
        )
        report = self.normalizer.normalize(payload)
        assert report is None
