# Data Schema

## Canonical WeatherReport Schema

```json
{
    "report_id": "uuid",
    "source_id": "string",
    "source_type": "api|dataset|web|social|citizen|replay|generator",
    "event_category": "rainfall|thunderstorm|flood|heatwave|fog|dust_storm|strong_wind|lightning|hail|cold_wave|other",
    "event_subcategory": "string|null",
    "timestamp": "ISO8601",
    "ingestion_timestamp": "ISO8601",
    "text": "string|null",
    "language": "string",
    "city": "string|null",
    "district": "string|null",
    "state": "string|null",
    "country": "string",
    "latitude": "float|null",
    "longitude": "float|null",
    "hashtags": ["string"],
    "image_urls": ["string"],
    "video_urls": ["string"],
    "source_url": "string|null",
    "author_id_hash": "string|null",
    "raw_payload_reference": "string|null",
    "is_simulated": "boolean",
    "schema_version": "string",
    "h3_index": "string|null",
    "h3_resolution": "int|null",
    "temperature_celsius": "float|null",
    "humidity_percent": "float|null",
    "rainfall_mm": "float|null",
    "wind_speed_kmh": "float|null",
    "wind_direction": "string|null",
    "pressure_hpa": "float|null",
    "visibility_km": "float|null",
    "severity": "int(1-10)|null",
    "quality_status": "pending|valid|warning|invalid|quarantined",
    "quality_notes": ["string"],
    "content_hash": "string",
    "extra_metadata": {}
}
```

## Database Tables

### sources
- source_id (PK)
- source_name, source_type, url, connector_type
- authentication_required, poll_interval_seconds
- reliability, geographic_coverage, rate_limits
- enabled, legal_notes, update_frequency
- health_status, last_successful_fetch, last_failure

### reports
- id (PK UUID), report_id (unique), source_id (FK)
- event_category, event_subcategory
- timestamp, ingestion_timestamp
- text, language, city, district, state, country
- latitude, longitude, location (PostGIS POINT)
- hashtags, image_urls, video_urls
- source_url, author_id_hash
- h3_index, h3_resolution
- temperature/humidity/rainfall/wind/pressure/visibility
- severity, quality_status, quality_notes
- content_hash, embedding (pgvector)

### report_relationships
- id (PK UUID)
- report_id_a (FK), report_id_b (FK)
- relationship_type, confidence
- metadata_json

### weather_events
- id (PK UUID), event_id (unique)
- event_category, status
- time_range_start/end
- center_latitude/longitude, center_location
- affected_area (PostGIS POLYGON)
- source_count, report_count, confidence_score
- h3_cells, severity

### event_reports
- event_id (FK), report_id (FK)

### event_cells
- event_id (FK), h3_index, h3_resolution

### data_quality
- Run statistics with timestamp
- total/valid/warning/invalid/quarantined counts

### ingestion_runs
- Run tracking per source
