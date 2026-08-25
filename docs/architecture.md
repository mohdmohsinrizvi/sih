# Architecture

## System Overview

The National Weather Big Data Analytics Platform processes weather-related data from multiple sources through a streaming pipeline, storing normalized and validated data in a centralized database for downstream AI/ML processing, event fusion, and visualization.

## Technology Choices

### Why Redpanda?
- Kafka-compatible API (no separate Kafka needed)
- Single binary deployment
- Better performance than Kafka for small to medium scale
- Lower operational complexity
- SSD-friendly storage engine

### Why PostgreSQL + PostGIS?
- Native geospatial support (PostGIS)
- pgvector for AI embedding storage
- Mature, battle-tested RDBMS
- Excellent indexing capabilities
- JSON support for flexible metadata

### Why H3?
- Uber's hierarchical spatial indexing
- Hexagonal grid avoids edge effects
- Fixed resolution cell IDs
- Efficient neighbor queries
- Industry-standard for geospatial analytics

### Why MinIO?
- S3-compatible object storage
- Free and open-source
- Stores raw payloads, media, replay datasets
- Avoids bloating PostgreSQL with binary data

### Why Redis?
- Fast in-memory cache
- Rate limiting state
- Health check caching
- Dashboard counters
- Not used as permanent database

### Why Replay?
- Deterministic testing
- Historical data replay at configurable speeds
- Demo scenarios without real API access
- Load testing at various speeds

### Why Synthetic Data?
- Prototype works without paid API keys
- Load testing at scale (10K-10M records)
- Deduplication pipeline demonstration
- Event clustering demonstration
- Always labeled as simulated

## Data Flow

```
Source → Connector → RawPayload → Normalizer → Validator → H3Indexer
    → Redpanda(normalized) → Pipeline → PostgreSQL
    → Deduplicator → Redpanda(dedup) → EventFusion → Redpanda(events)
```

## Prototype vs Production

### Prototype (Local Docker)
- Single PostgreSQL instance
- Single Redpanda broker
- Single MinIO instance
- In-memory dedup state
- Local filesystem replay

### National Production
- PostgreSQL cluster with read replicas
- Multi-broker Redpanda/Kafka cluster
- Distributed MinIO (erasure coding)
- Redis Cluster for distributed state
- Kubernetes orchestration
- Regional processing nodes
- CDN for media delivery
- Dedicated AI inference cluster
