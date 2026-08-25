import pytest
import asyncio
from datetime import datetime, timezone


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_report_data():
    return {
        "report_id": "test-001",
        "source_id": "citizen_report",
        "source_type": "citizen",
        "event_category": "rainfall",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "text": "Heavy rainfall in Lucknow, streets waterlogged",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "country": "India",
        "latitude": 26.8467,
        "longitude": 80.9462,
        "hashtags": ["#IMD", "#Rainfall", "#Lucknow"],
        "temperature_celsius": 28.5,
        "humidity_percent": 85.0,
        "rainfall_mm": 45.0,
        "severity": 6,
        "is_simulated": True,
    }


@pytest.fixture
def sample_api_payload():
    return {
        "source_id": "imd_api",
        "source_type": "api",
        "data": {
            "station": "Delhi",
            "temp": 42.5,
            "humidity": 35,
            "wind_speed": 12,
            "description": "Heatwave conditions in Delhi",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_social_payload():
    return {
        "source_id": "social_media",
        "source_type": "social",
        "text": "Flood water entering homes in Guwahati #Flood #Assam",
        "hashtags": ["#Flood", "#Assam", "#IMD"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": {"lat": 26.1445, "lon": 91.7362},
    }
