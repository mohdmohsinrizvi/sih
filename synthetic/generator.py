from __future__ import annotations

import hashlib
import random
import uuid
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Iterator
from dataclasses import dataclass

import structlog
import orjson

from schemas.weather_report import WeatherReport, EventCategory, SourceType

logger = structlog.get_logger(__name__)

INDIAN_CITIES = [
    {"city": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lon": 80.9462, "district": "Lucknow"},
    {"city": "Delhi", "state": "Delhi", "lat": 28.7041, "lon": 77.1025, "district": "New Delhi"},
    {"city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lon": 72.8777, "district": "Mumbai"},
    {"city": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lon": 88.3639, "district": "Kolkata"},
    {"city": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707, "district": "Chennai"},
    {"city": "Bangalore", "state": "Karnataka", "lat": 12.9716, "lon": 77.5946, "district": "Bangalore Urban"},
    {"city": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lon": 78.4867, "district": "Hyderabad"},
    {"city": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lon": 72.5714, "district": "Ahmedabad"},
    {"city": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567, "district": "Pune"},
    {"city": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lon": 75.7873, "district": "Jaipur"},
    {"city": "Guwahati", "state": "Assam", "lat": 26.1445, "lon": 91.7362, "district": "Kamrup"},
    {"city": "Patna", "state": "Bihar", "lat": 25.6093, "lon": 85.1376, "district": "Patna"},
    {"city": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lon": 77.4126, "district": "Bhopal"},
    {"city": "Thiruvananthapuram", "state": "Kerala", "lat": 8.5241, "lon": 76.9366, "district": "Thiruvananthapuram"},
    {"city": "Chandigarh", "state": "Chandigarh", "lat": 30.7333, "lon": 76.7794, "district": "Chandigarh"},
    {"city": "Indore", "state": "Madhya Pradesh", "lat": 22.7196, "lon": 75.8577, "district": "Indore"},
    {"city": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lon": 79.0882, "district": "Nagpur"},
    {"city": "Visakhapatnam", "state": "Andhra Pradesh", "lat": 17.6868, "lon": 83.2185, "district": "Visakhapatnam"},
    {"city": "Surat", "state": "Gujarat", "lat": 21.1702, "lon": 72.8311, "district": "Surat"},
    {"city": "Kanpur", "state": "Uttar Pradesh", "lat": 26.4499, "lon": 80.3319, "district": "Kanpur Nagar"},
    {"city": "Jodhpur", "state": "Rajasthan", "lat": 26.2389, "lon": 73.0243, "district": "Jodhpur"},
    {"city": "Amritsar", "state": "Punjab", "lat": 31.6340, "lon": 74.8723, "district": "Amritsar"},
    {"city": "Ranchi", "state": "Jharkhand", "lat": 23.3441, "lon": 85.3096, "district": "Ranchi"},
    {"city": "Varanasi", "state": "Uttar Pradesh", "lat": 25.3176, "lon": 82.9739, "district": "Varanasi"},
    {"city": "Coimbatore", "state": "Tamil Nadu", "lat": 11.0168, "lon": 76.9558, "district": "Coimbatore"},
    {"city": "Madurai", "state": "Tamil Nadu", "lat": 9.9252, "lon": 78.1198, "district": "Madurai"},
    {"city": "Agra", "state": "Uttar Pradesh", "lat": 27.1767, "lon": 78.0081, "district": "Agra"},
    {"city": "Nashik", "state": "Maharashtra", "lat": 19.9975, "lon": 73.7898, "district": "Nashik"},
    {"city": "Udaipur", "state": "Rajasthan", "lat": 24.5854, "lon": 73.7125, "district": "Udaipur"},
    {"city": "Shillong", "state": "Meghalaya", "lat": 25.5788, "lon": 91.8933, "district": "East Khasi Hills"},
    {"city": "Imphal", "state": "Manipur", "lat": 24.8170, "lon": 93.9368, "district": "Imphal West"},
    {"city": "Gangtok", "state": "Sikkim", "lat": 27.3389, "lon": 88.6065, "district": "East Sikkim"},
    {"city": "Itanagar", "state": "Arunachal Pradesh", "lat": 27.1044, "lon": 93.6920, "district": "Papum Pare"},
    {"city": "Aizawl", "state": "Mizoram", "lat": 23.7271, "lon": 92.7176, "district": "Aizawl"},
    {"city": "Kohima", "state": "Nagaland", "lat": 25.6586, "lon": 94.1086, "district": "Kohima"},
    {"city": "Agartala", "state": "Tripura", "lat": 23.8315, "lon": 91.2868, "district": "West Tripura"},
    {"city": "Panaji", "state": "Goa", "lat": 15.4909, "lon": 73.8278, "district": "North Goa"},
    {"city": "Dehradun", "state": "Uttarakhand", "lat": 30.3165, "lon": 78.0322, "district": "Dehradun"},
    {"city": "Raipur", "state": "Chhattisgarh", "lat": 21.2514, "lon": 81.6296, "district": "Raipur"},
]

WEATHER_TEMPLATES = {
    EventCategory.RAINFALL: [
        "Heavy rainfall reported in {city}. Streets waterlogged.",
        "Continuous rain since morning in {city}. {rainfall}mm recorded.",
        "Monsoon showers intensifying in {city}, {state}. Roads flooded.",
        "Moderate rainfall in {city} district. Farmers relieved.",
        "Sudden downpour in {city} causing traffic disruptions.",
    ],
    EventCategory.FLOOD: [
        "Severe flooding in {city} areas. Water levels rising.",
        "River {river} overflowing near {city}. Evacuations underway.",
        "Flood situation worsens in {city}, {state}. NDRF deployed.",
        "Flash floods in {city} after heavy overnight rainfall.",
        "Low-lying areas of {city} submerged. Relief camps opened.",
    ],
    EventCategory.THUNDERSTORM: [
        "Severe thunderstorm in {city}. Trees uprooted.",
        "Thunderstorm with gusty winds hits {city}. Power outages reported.",
        "Intense thunder and lightning activity over {city}.",
        "Thunderstorm warning for {city}, {state}. Stay indoors.",
    ],
    EventCategory.HEATWAVE: [
        "Heatwave conditions in {city}. Temperature touching {temp}°C.",
        "Severe heatwave in {city}, {state}. Water shortage reported.",
        "Mercury rises to {temp}°C in {city}. Heat advisory issued.",
        "Scorching heat in {city}. Public advised to stay hydrated.",
    ],
    EventCategory.FOG: [
        "Dense fog in {city} reducing visibility to {visibility}m.",
        "Fog disrupts flights and trains in {city}.",
        "Thick fog blankets {city}. Road accidents reported.",
        "Morning fog in {city}, {state}. Traffic moving slowly.",
    ],
    EventCategory.DUST_STORM: [
        "Dust storm hits {city}. Visibility near zero.",
        "Severe dust storm in {city}, {state}. Flights diverted.",
        "Sandstorm engulfs {city}. Outdoor activities halted.",
        "Dust storm with strong winds lashes {city}.",
    ],
    EventCategory.STRONG_WIND: [
        "Strong winds of {wind} km/h reported in {city}.",
        "Gusty winds cause damage in {city}, {state}.",
        "High wind advisory for {city}. Secure loose objects.",
        "Cyclonic winds approaching {city}. Precautions advised.",
    ],
    EventCategory.LIGHTNING: [
        "Lightning strike in {city} injures 3 people.",
        "Frequent lightning over {city} district.",
        "Lightning activity intensifies in {city}, {state}.",
    ],
    EventCategory.HAIL: [
        "Hailstorm damages crops in {city} area.",
        "Heavy hail in {city}. Vehicles damaged.",
        "Hailstones pelt {city}, {state}. Agricultural losses feared.",
    ],
    EventCategory.COLD_WAVE: [
        "Cold wave grips {city}. Temperature drops to {temp}°C.",
        "Severe cold in {city}, {state}. Homeless shelters full.",
        "Frost reported in {city} outskirts. Roads slippery.",
    ],
    EventCategory.OTHER: [
        "Unusual weather patterns observed in {city}.",
        "Weather alert for {city}, {state}. Stay updated.",
    ],
}

RIVERS = ["Ganga", "Yamuna", "Brahmaputra", "Narmada", "Godavari", "Krishna", "Mahanadi", "Son", "Chambal"]

HASHTAGS_BY_CATEGORY = {
    EventCategory.RAINFALL: ["#IMD", "#Rainfall", "#Monsoon", "#HeavyRain"],
    EventCategory.FLOOD: ["#IMD", "#Flood", "#FloodAlert", "#Emergency"],
    EventCategory.THUNDERSTORM: ["#IMD", "#Thunderstorm", "#Storm", "#Lightning"],
    EventCategory.HEATWAVE: ["#IMD", "#Heatwave", "#Heat", "#Summer"],
    EventCategory.FOG: ["#IMD", "#Fog", "#LowVisibility", "#Winter"],
    EventCategory.DUST_STORM: ["#IMD", "#DustStorm", "#Sandstorm"],
    EventCategory.STRONG_WIND: ["#IMD", "#StrongWind", "#Cyclone", "#WindAlert"],
    EventCategory.LIGHTNING: ["#IMD", "#Lightning", "#Thunder"],
    EventCategory.HAIL: ["#IMD", "#Hail", "#Hailstorm"],
    EventCategory.COLD_WAVE: ["#IMD", "#ColdWave", "#Frost", "#Winter"],
    EventCategory.OTHER: ["#IMD", "#Weather"],
}

SOURCE_TYPES = [SourceType.API, SourceType.CITIZEN, SourceType.SOCIAL, SourceType.WEB]


@dataclass
class SyntheticConfig:
    total_records: int = 10000
    batch_size: int = 1000
    duplicate_ratio: float = 0.3
    near_duplicate_ratio: float = 0.2
    cluster_ratio: float = 0.15
    seed: int = 42
    event_distribution: Optional[dict] = None
    start_time: Optional[datetime] = None
    time_span_hours: int = 24


class SyntheticWeatherGenerator:
    def __init__(self, config: Optional[SyntheticConfig] = None):
        self.config = config or SyntheticConfig()
        self.rng = random.Random(self.config.seed)
        self._uuid_counter = 0

        if self.config.event_distribution is None:
            self.config.event_distribution = {
                EventCategory.RAINFALL: 0.25,
                EventCategory.FLOOD: 0.10,
                EventCategory.THUNDERSTORM: 0.15,
                EventCategory.HEATWAVE: 0.12,
                EventCategory.FOG: 0.08,
                EventCategory.DUST_STORM: 0.05,
                EventCategory.STRONG_WIND: 0.08,
                EventCategory.LIGHTNING: 0.07,
                EventCategory.HAIL: 0.05,
                EventCategory.COLD_WAVE: 0.03,
                EventCategory.OTHER: 0.02,
            }

    def generate(self) -> Iterator[dict]:
        if self.config.start_time is None:
            self.config.start_time = datetime.now(timezone.utc) - timedelta(hours=self.config.time_span_hours)

        original_count = int(self.config.total_records * (1 - self.config.duplicate_ratio - self.config.near_duplicate_ratio))
        duplicate_count = int(self.config.total_records * self.config.duplicate_ratio)
        near_dup_count = int(self.config.total_records * self.config.near_duplicate_ratio)

        cluster_count = int(original_count * self.config.cluster_ratio)
        non_cluster_count = original_count - cluster_count

        batch = []
        yield from self._generate_cluster_events(cluster_count)
        yield from self._generate_scattered_events(non_cluster_count)

        yield from self._generate_duplicates(duplicate_count)
        yield from self._generate_near_duplicates(near_dup_count)

    def _generate_cluster_events(self, count: int) -> Iterator[dict]:
        cluster_cities = self.rng.sample(INDIAN_CITIES, min(5, len(INDIAN_CITIES)))
        generated = 0
        per_city = count // len(cluster_cities)
        remainder = count % len(cluster_cities)

        for idx, city_info in enumerate(cluster_cities):
            if generated >= count:
                break
            category = self._weighted_category()
            base_time = self.config.start_time + timedelta(
                minutes=self.rng.randint(0, self.config.time_span_hours * 60)
            )
            city_count = per_city + (1 if idx < remainder else 0)

            for i in range(city_count):
                if generated >= count:
                    break
                lat_offset = self.rng.gauss(0, 0.02)
                lon_offset = self.rng.gauss(0, 0.02)
                time_offset = timedelta(minutes=self.rng.randint(0, 60))

                report = self._create_report(
                    city_info=city_info,
                    category=category,
                    timestamp=base_time + time_offset,
                    lat_offset=lat_offset,
                    lon_offset=lon_offset,
                    is_cluster=True,
                )
                self._uuid_counter += 1
                generated += 1
                yield report

    def _generate_scattered_events(self, count: int) -> Iterator[dict]:
        for _ in range(count):
            city_info = self.rng.choice(INDIAN_CITIES)
            category = self._weighted_category()
            time_offset = timedelta(
                minutes=self.rng.randint(0, self.config.time_span_hours * 60)
            )
            timestamp = self.config.start_time + time_offset

            report = self._create_report(
                city_info=city_info,
                category=category,
                timestamp=timestamp,
            )
            self._uuid_counter += 1
            yield report

    def _generate_duplicates(self, count: int) -> Iterator[dict]:
        originals = []
        for _ in range(min(count, 100)):
            city_info = self.rng.choice(INDIAN_CITIES)
            category = self._weighted_category()
            timestamp = self.config.start_time + timedelta(
                minutes=self.rng.randint(0, self.config.time_span_hours * 60)
            )
            originals.append(self._create_report(
                city_info=city_info,
                category=category,
                timestamp=timestamp,
            ))

        for _ in range(count):
            original = self.rng.choice(originals)
            dup = dict(original)
            dup["report_id"] = str(uuid.uuid4())
            dup["is_simulated"] = True
            dup["extra_metadata"] = {**dup.get("extra_metadata", {}), "duplicate_type": "exact"}
            yield dup

    def _generate_near_duplicates(self, count: int) -> Iterator[dict]:
        originals = []
        for _ in range(min(count, 100)):
            city_info = self.rng.choice(INDIAN_CITIES)
            category = self._weighted_category()
            timestamp = self.config.start_time + timedelta(
                minutes=self.rng.randint(0, self.config.time_span_hours * 60)
            )
            originals.append(self._create_report(
                city_info=city_info,
                category=category,
                timestamp=timestamp,
            ))

        for _ in range(count):
            original = self.rng.choice(originals)
            near_dup = dict(original)
            near_dup["report_id"] = str(uuid.uuid4())

            if near_dup.get("text") and self.rng.random() < 0.5:
                words = near_dup["text"].split()
                if len(words) > 3:
                    idx = self.rng.randint(0, len(words) - 1)
                    words[idx] = words[idx] + "!"
                    near_dup["text"] = " ".join(words)

            if near_dup.get("latitude"):
                near_dup["latitude"] = near_dup["latitude"] + self.rng.gauss(0, 0.005)
                near_dup["longitude"] = near_dup["longitude"] + self.rng.gauss(0, 0.005)

            if near_dup.get("timestamp"):
                ts = datetime.fromisoformat(near_dup["timestamp"].replace("Z", "+00:00"))
                ts = ts + timedelta(minutes=self.rng.randint(-5, 5))
                near_dup["timestamp"] = ts.isoformat()

            near_dup["is_simulated"] = True
            near_dup["extra_metadata"] = {**near_dup.get("extra_metadata", {}), "duplicate_type": "near_duplicate"}
            yield near_dup

    def _create_report(
        self,
        city_info: dict,
        category: EventCategory,
        timestamp: datetime,
        lat_offset: float = 0,
        lon_offset: float = 0,
        is_cluster: bool = False,
    ) -> dict:
        templates = WEATHER_TEMPLATES.get(category, WEATHER_TEMPLATES[EventCategory.OTHER])
        template = self.rng.choice(templates)

        city = city_info["city"]
        state = city_info["state"]
        river = self.rng.choice(RIVERS)
        temp = self.rng.randint(38, 48) if category == EventCategory.HEATWAVE else self.rng.randint(5, 25)
        rainfall = self.rng.randint(50, 200) if category in (EventCategory.RAINFALL, EventCategory.FLOOD) else 0
        wind = self.rng.randint(40, 120) if category in (EventCategory.STRONG_WIND, EventCategory.THUNDERSTORM) else 0
        visibility = self.rng.randint(50, 500) if category == EventCategory.FOG else 1000

        text = template.format(
            city=city, state=state, river=river, temp=temp,
            rainfall=rainfall, wind=wind, visibility=visibility,
        )

        hashtags = list(self.rng.sample(
            HASHTAGS_BY_CATEGORY.get(category, ["#IMD"]),
            k=min(self.rng.randint(1, 3), len(HASHTAGS_BY_CATEGORY.get(category, ["#IMD"]))),
        ))
        city_tag = f"#{city.replace(' ', '')}"
        if city_tag not in hashtags:
            hashtags.append(city_tag)

        source_type = self.rng.choice(SOURCE_TYPES)

        lat = city_info["lat"] + lat_offset
        lon = city_info["lon"] + lon_offset

        severity = self._infer_severity(category)

        report = {
            "report_id": str(uuid.uuid4()),
            "source_id": f"synthetic_{source_type.value}",
            "source_type": source_type.value,
            "event_category": category.value,
            "event_subcategory": None,
            "timestamp": timestamp.isoformat(),
            "text": text,
            "language": self.rng.choice(["en", "hi"]),
            "city": city,
            "district": city_info["district"],
            "state": state,
            "country": "India",
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "hashtags": hashtags,
            "image_urls": [],
            "video_urls": [],
            "source_url": f"https://synthetic.example.com/report/{uuid.uuid4().hex[:8]}",
            "author_id_hash": hashlib.sha256(uuid.uuid4().hex.encode()).hexdigest()[:16],
            "raw_payload_reference": None,
            "is_simulated": True,
            "schema_version": "1.0",
            "temperature_celsius": float(temp) if category in (EventCategory.HEATWAVE, EventCategory.COLD_WAVE) else None,
            "humidity_percent": float(self.rng.randint(30, 95)) if category in (EventCategory.RAINFALL, EventCategory.FLOOD, EventCategory.FOG) else None,
            "rainfall_mm": float(rainfall) if rainfall > 0 else None,
            "wind_speed_kmh": float(wind) if wind > 0 else None,
            "severity": severity,
            "_timestamp": timestamp.timestamp(),
            "extra_metadata": {
                "is_cluster_event": is_cluster,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        return report

    def _weighted_category(self) -> EventCategory:
        categories = list(self.config.event_distribution.keys())
        weights = list(self.config.event_distribution.values())
        return self.rng.choices(categories, weights=weights, k=1)[0]

    def _infer_severity(self, category: EventCategory) -> int:
        severity_ranges = {
            EventCategory.RAINFALL: (3, 8),
            EventCategory.FLOOD: (6, 10),
            EventCategory.THUNDERSTORM: (4, 8),
            EventCategory.HEATWAVE: (5, 9),
            EventCategory.FOG: (2, 5),
            EventCategory.DUST_STORM: (5, 8),
            EventCategory.STRONG_WIND: (5, 9),
            EventCategory.LIGHTNING: (4, 8),
            EventCategory.HAIL: (4, 7),
            EventCategory.COLD_WAVE: (3, 7),
            EventCategory.OTHER: (1, 5),
        }
        low, high = severity_ranges.get(category, (1, 5))
        return self.rng.randint(low, high)

    def generate_to_file(self, filepath: str, count: Optional[int] = None) -> str:
        if count:
            self.config.total_records = count

        start = time.time()
        records_written = 0

        with open(filepath, "wb") as f:
            for report in self.generate():
                line = orjson.dumps(report) + b"\n"
                f.write(line)
                records_written += 1

        elapsed = time.time() - start
        logger.info(
            "synthetic_data_generated",
            records=records_written,
            file=filepath,
            duration_seconds=round(elapsed, 2),
            records_per_second=round(records_written / elapsed, 1) if elapsed > 0 else 0,
        )

        return filepath

    def generate_batches(self) -> Iterator[list[dict]]:
        batch = []
        for report in self.generate():
            batch.append(report)
            if len(batch) >= self.config.batch_size:
                yield batch
                batch = []
        if batch:
            yield batch
