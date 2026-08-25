# SIH Demo Guide

## Quick Start

```bash
# 1. Start infrastructure
docker compose up -d postgres redpanda redis minio

# 2. Install Python dependencies
pip install -e .

# 3. Generate synthetic data
python -m cli.main generate --records 10000

# 4. Process through pipeline
python -m cli.main pipeline process --file data/replay/synthetic.ndjson --batch-size 500

# 5. Start API
uvicorn api.main:app --host 0.0.0.0 --port 8000

# 6. Open API docs
open http://localhost:8000/docs
```

## Demo Scenarios

### Scenario 1: Lucknow Flood Event
- 500 reports from 40 sources
- Multiple nearby H3 cells
- 30-minute time window
- Duplicates detected
- Event candidate created

### Scenario 2: Delhi Heatwave
- 300 reports from 25 sources
- Temperature > 42°C
- Heat-related hashtags
- Source diversity verified

### Scenario 3: Mumbai Heavy Rainfall
- 400 reports from 35 sources
- Rainfall measurements
- Waterlogging reports
- Geographic clustering

### Scenario 4: Assam Flood
- 350 reports from 30 sources
- Brahmaputra river flooding
- Evacuation reports
- Multi-district coverage

### Scenario 5: Rajasthan Dust Storm
- 200 reports from 15 sources
- Visibility reduction
- Wind damage
- Agricultural impact

## API Endpoints for Demo

```bash
# List sources
curl http://localhost:8000/sources

# Get reports
curl http://localhost:8000/reports?limit=10

# Get events
curl http://localhost:8000/events/candidates

# Data quality
curl http://localhost:8000/data-quality

# Generate more data
curl -X POST "http://localhost:8000/synthetic/generate?records=50000"

# Pipeline status
curl http://localhost:8000/pipeline/status
```

## Metrics to Show

1. Records received and processed
2. Records per second throughput
3. Normalization success rate
4. Validation pass/warn/fail rates
5. H3 cell distribution
6. Duplicate candidates detected
7. Event candidates generated
8. Source diversity per event
9. Geographic coverage map
10. Time-series analysis
