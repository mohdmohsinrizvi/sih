# 🌦️ National Weather Big Data Analytics Platform

**Smart India Hackathon 2024 — Problem Statement #26069**

A zero-cost, open-source platform for ingesting, normalizing, deduplicating, and analyzing multi-source weather data across India at scale.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Data Pipeline](#data-pipeline)
- [Deployment](#deployment)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

India experiences devastating weather events annually — floods, heatwaves, fog, and cyclones — causing significant loss of life and property. The core problem is the **fragmentation of weather data** across disparate sources with inconsistent formats, making real-time analysis and early warning systems nearly impossible.

This platform solves that by providing:

- **Multi-source ingestion** — REST APIs, social media, citizen reports, CSV/JSON datasets
- **Automated normalization** — Cleans, standardizes, and structures raw data
- **Intelligent deduplication** — Exact, near-match, and geo-temporal duplicate detection
- **Event fusion** — Groups related reports into weather events with confidence scoring
- **Geospatial indexing** — H3 hexagonal grid for efficient spatial queries
- **Full-text search** — PostgreSQL with pg_trgm for Hindi/English text search

**Zero budget. 100% open-source. Production-ready architecture.**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
├──────────┬──────────┬──────────┬──────────┬────────────────────┤
│ IMD API  │ OpenWeather│ Social  │ Citizen  │ CSV/JSON Datasets  │
│ (future) │ (future)  │ Media   │ Reports  │ (NOAA, etc.)       │
└────┬─────┴────┬─────┴────┬────┴────┬─────┴────────┬───────────┘
     │          │          │         │               │
     ▼          ▼          ▼         ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMING LAYER                              │
│                  Apache Kafka (Redpanda)                        │
│         weather.raw → weather.normalized → weather.events       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PROCESSING PIPELINE                         │
├─────────┬─────────┬─────────┬─────────┬────────────────────────┤
│ Normalize│Validate │ H3 Index│  Dedup  │   Event Fusion         │
│ & Clean  │ & QA    │ & Geo  │ & Match │   & Clustering         │
└─────────┴─────────┴─────────┴─────────┴────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                              │
├──────────────────┬──────────────────┬──────────────────────────┤
│   PostgreSQL     │      Redis       │        MinIO              │
│  + PostGIS       │  (Cache/Sessions)│   (Object Storage)        │
│  + pgvector      │                  │                           │
│  + pg_trgm       │                  │                           │
└──────────────────┴──────────────────┴──────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API LAYER                                 │
│                   FastAPI (async, auto-docs)                    │
│              /reports  /events  /data-quality  /stats           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Description | Status |
|---------|-------------|--------|
| Multi-format Ingestion | JSON, CSV, NDJSON, REST API, RSS, Citizen | ✅ |
| Real-time Streaming | Kafka-compatible message queue (Redpanda) | ✅ |
| Data Normalization | Text cleaning, timestamp parsing, GPS validation | ✅ |
| Quality Validation | Required field checks, severity inference | ✅ |
| H3 Geospatial Index | Hexagonal grid indexing (resolution 0-15) | ✅ |
| 3-Level Deduplication | Exact hash, Levenshtein text, geo-temporal | ✅ |
| Event Fusion | Cluster reports into weather events | ✅ |
| PostGIS Integration | Spatial queries, bounding box, nearest neighbor | ✅ |
| pgvector Embeddings | 384-dim vectors for semantic search | ✅ |
| Synthetic Data Generator | Configurable fake data for testing | ✅ |
| Replay Engine | Deterministic replay with speed control | ✅ |
| REST API | 20+ endpoints with auto-generated docs | ✅ |
| Docker Compose | One-command infrastructure setup | ✅ |
| Prometheus Metrics | Monitoring and observability | ✅ |
| CLI Interface | Command-line tools for all operations | ✅ |

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.12+ | Core runtime |
| API Framework | FastAPI | Async REST API with auto-docs |
| Message Queue | Redpanda | Kafka-compatible streaming |
| Database | PostgreSQL 16 | Primary data store |
| Extensions | PostGIS, pgvector, pg_trgm | Geo, vectors, text search |
| ORM | SQLAlchemy 2.0 | Async database access |
| Migrations | Alembic | Schema versioning |
| Cache | Redis | Session caching, rate limiting |
| Object Storage | MinIO | S3-compatible file storage |
| Validation | Pydantic v2 | Data models and validation |
| HTTP Client | httpx | Async HTTP requests |
| Kafka Client | confluent-kafka | Producer/consumer |
| Geospatial | h3-py | Hexagonal indexing |
| Serialization | orjson | Fast JSON parsing |
| Logging | structlog | Structured logging |
| Containerization | Docker Compose | Multi-service orchestration |
| Monitoring | Prometheus | Metrics and alerting |

---

## Project Structure

```
sih/
├── api/                        # FastAPI application
│   └── main.py                 # Routes, middleware, lifespan
│
├── cli/                        # Command-line interface
│   └── main.py                 # Click-based CLI commands
│
├── config/                     # Configuration
│   ├── settings.py             # Pydantic settings (env vars)
│   └── sources.yaml            # Data source definitions
│
├── connectors/                 # Data source connectors
│   ├── base.py                 # Base + REST/CSV/JSON/NDJSON connectors
│   └── registry.py             # Source registry and config
│
├── data_engine/                # Core data processing
│   ├── normalization/          # Text cleaning, field extraction
│   │   └── normalizer.py
│   ├── quality/                # Validation and QA
│   │   └── validator.py
│   ├── h3/                     # Geospatial indexing
│   │   └── indexer.py
│   ├── dedup/                  # Deduplication engine
│   │   └── deduplicator.py
│   └── event_fusion/           # Event clustering
│       └── candidate_generator.py
│
├── streaming/                  # Kafka/Redpanda integration
│   └── redpanda.py             # Producer, consumer, topic config
│
├── storage/                    # Database layer
│   ├── database.py             # Async SQLAlchemy engine
│   └── models.py               # ORM models (10 tables)
│
├── schemas/                    # Pydantic models
│   └── weather_report.py       # Canonical WeatherReport schema
│
├── pipeline/                   # Pipeline orchestrator
│   └── processor.py            # Full ingestion pipeline
│
├── synthetic/                  # Test data generation
│   └── generator.py            # Configurable synthetic generator
│
├── replay_engine/              # Data replay
│   └── engine.py               # Speed-controlled replay
│
├── metrics/                    # Monitoring
│   └── prometheus.py           # Prometheus metrics
│
├── tests/                      # Test suite (53 tests)
│   ├── test_normalizer.py
│   ├── test_validator.py
│   ├── test_h3_indexer.py
│   ├── test_dedup.py
│   ├── test_event_fusion.py
│   └── ...
│
├── scripts/                    # SQL initialization
│   └── init-db.sql
│
├── data/                       # Runtime data (gitignored)
│   └── replay/
│
├── docker-compose.yml          # Infrastructure orchestration
├── Dockerfile                  # Backend container
├── Dockerfile.postgres         # PostgreSQL + PostGIS + pgvector
├── pyproject.toml              # Python dependencies
├── alembic.ini                 # Migration config
├── demo.py                     # One-command demo script
└── README.md                   # This file
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose v2+
- Python 3.12+
- 4 GB RAM minimum

### 1. Clone & Setup

```bash
git clone https://github.com/mohdmohsinrizvi/sih.git
cd sih
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Start Infrastructure

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432) with PostGIS + pgvector
- Redpanda (port 19092) — Kafka-compatible streaming
- Redis (port 6379) — caching
- MinIO (port 9000/9001) — object storage

### 3. Initialize Database

```bash
docker exec weather-postgres psql -U weather -d weatherdb -c \
  "CREATE EXTENSION IF NOT EXISTS postgis; \
   CREATE EXTENSION IF NOT EXISTS vector; \
   CREATE EXTENSION IF NOT EXISTS pg_trgm;"

python -c "import asyncio; from storage.database import init_db; asyncio.run(init_db())"
```

### 4. Run Demo

```bash
python demo.py
```

This executes the full pipeline end-to-end: generates synthetic data, processes 1000 records, and displays results.

### 5. Access API

```bash
# Health check
curl http://localhost:8000/health

# Swagger documentation
open http://localhost:8000/docs
```

---

## API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Platform information |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI (interactive docs) |
| `GET` | `/redoc` | ReDoc documentation |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/reports` | List reports (paginated, filterable) |
| `GET` | `/reports/{report_id}` | Get single report with full details |

**Query Parameters:**
- `limit` (1-1000, default 50)
- `offset` (default 0)
- `state` — Filter by Indian state
- `city` — Filter by city
- `event_category` — rainfall, flood, fog, heatwave, etc.
- `quality_status` — valid, warning, invalid

### Events

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/events/candidates` | List detected weather events |

### Sources

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/sources` | List all registered sources |
| `GET` | `/sources/{source_id}` | Get source details |
| `GET` | `/sources/health` | Source health summary |

### Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ingestion/status` | Pipeline status and metrics |
| `GET` | `/ingestion/statistics` | Processing statistics |
| `POST` | `/pipeline/process-batch` | Process a batch of reports |

### Data Quality

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/data-quality` | Quality report (valid/warning/invalid counts) |
| `GET` | `/stats/summary` | Overall platform statistics |

### Synthetic Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/synthetic/generate` | Generate synthetic records |

**Parameters:** `records` (1-1000000), `seed` (default 42)

### Replay Engine

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/replay/status` | Replay engine status |
| `POST` | `/replay/start` | Start data replay |
| `POST` | `/replay/pause` | Pause replay |
| `POST` | `/replay/resume` | Resume replay |
| `POST` | `/replay/stop` | Stop replay |

---

## Data Pipeline

### Pipeline Stages

```
1. INGESTION        Raw data from multiple sources
        ↓
2. NORMALIZATION    Clean text, parse timestamps, validate GPS
        ↓
3. VALIDATION       Check required fields, infer severity
        ↓
4. H3 INDEXING      Generate hexagonal spatial index
        ↓
5. DEDUPLICATION    Exact hash + Levenshtein + geo-temporal matching
        ↓
6. EVENT FUSION     Cluster related reports into weather events
        ↓
7. STORAGE          PostgreSQL + PostGIS + pgvector
```

### Deduplication Strategy

| Level | Method | Threshold |
|-------|--------|-----------|
| L1 | Content hash (SHA-256) | Exact match |
| L2 | Levenshtein distance | >90% similarity |
| L3 | Geo-temporal | Same H3 cell + time window |

### Event Categories

| Category | Keywords |
|----------|----------|
| `rainfall` | rain, rainfall, precipitation, drizzle, shower |
| `flood` | flood, flooding, deluge, waterlogging |
| `heatwave` | heatwave, heat wave, scorching, extreme heat |
| `fog` | fog, mist, haze, low visibility, smog |
| `thunderstorm` | thunder, lightning, tempest |
| `dust_storm` | dust storm, sandstorm |
| `strong_wind` | wind, gale, cyclone, gusty |
| `cold_wave` | cold wave, frost, freeze |

---

## Deployment

### Local Development

```bash
docker-compose up -d
python demo.py
```

### Production (Docker)

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f backend

# Scale workers
docker-compose up -d --scale backend=3
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://weather:weather@localhost:5432/weatherdb` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `REDPANDA_BOOTSTRAP_SERVERS` | `localhost:19092` | Redpanda/Kafka brokers |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO endpoint |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO access key |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO secret key |
| `IMD_API_KEY` | — | IMD API key (optional) |
| `OPENWEATHER_API_KEY` | — | OpenWeatherMap key (optional) |

---

## Roadmap

### Phase 1 — Current (Data Engineering) ✅
- [x] Multi-source ingestion pipeline
- [x] Data normalization and validation
- [x] H3 geospatial indexing
- [x] 3-level deduplication
- [x] Event fusion and clustering
- [x] PostgreSQL + PostGIS + pgvector storage
- [x] FastAPI REST endpoints
- [x] Docker Compose infrastructure
- [x] Synthetic data generator
- [x] Replay engine
- [x] CLI interface

### Phase 2 — AI/ML Integration (Planned)
- [ ] Transformer-based NER for Hindi/English weather text
- [ ] Sentiment analysis for severity scoring
- [ ] Embedding-based semantic search (pgvector)
- [ ] Time-series forecasting (Prophet/LSTM)
- [ ] Anomaly detection in weather patterns
- [ ] Multi-language text classification
- [ ] Image analysis for citizen-submitted photos

### Phase 3 — Frontend (Planned)
- [ ] React/Next.js dashboard
- [ ] Interactive map (Leaflet/Mapbox)
- [ ] Real-time data visualization (D3.js/Recharts)
- [ ] Alert management system
- [ ] Historical data explorer
- [ ] Admin panel for source management

### Phase 4 — Advanced Features (Planned)
- [ ] Apache Spark for batch analytics
- [ ] Grafana dashboards
- [ ] Mobile app (React Native)
- [ ] WhatsApp/SMS alert integration
- [ ] CI/CD pipeline
- [ ] Kubernetes deployment

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Run linter
python -m ruff check .

# Run type checker
python -m mypy .
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Smart India Hackathon 2024** for the problem statement
- **PostGIS** for geospatial capabilities
- **H3** by Uber for hexagonal indexing
- **Redpanda** for Kafka-compatible streaming
- **FastAPI** for the async API framework

---

**Built with ❤️ for India's weather resilience**
