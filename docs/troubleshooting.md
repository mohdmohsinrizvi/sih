# Troubleshooting Guide

## Common Issues

### PostgreSQL won't start
```bash
# Check logs
docker compose logs postgres

# Ensure port 5432 is free
lsof -i :5432

# Reset volume
docker compose down -v
docker compose up -d postgres
```

### Redpanda connection issues
```bash
# Check Redpanda health
docker compose logs redpanda

# Test connection
rpk cluster health --api-urls localhost:9644

# Check topics
rpk topic list --api-urls localhost:9644
```

### MinIO bucket not created
```bash
# Access MinIO console
open http://localhost:9001

# Create bucket manually
mc alias set local localhost:9000 minioadmin minioadmin
mc mb local/weather-data
```

### Python import errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/home/mohsin/Desktop/SIH

# Reinstall dependencies
pip install -e ".[dev]"
```

### H3 extension not found in PostgreSQL
```bash
# Install h3 extension
docker compose exec postgres psql -U weather -d weatherdb -c "CREATE EXTENSION IF NOT EXISTS h3;"
```

### Tests failing
```bash
# Run with verbose output
python -m pytest tests/ -v --tb=long

# Run specific test
python -m pytest tests/test_schema.py -v
```

## Performance Tuning

### Increase batch size
```bash
python -m cli.main pipeline process --file data/replay/synthetic.ndjson --batch-size 1000
```

### Increase Redpanda throughput
- Increase `linger.ms` in producer config
- Increase `batch.size` for producer
- Add more partitions to topics

### Database performance
- Ensure proper indexes exist (auto-created by SQLAlchemy)
- Increase `pool_size` in database.py
- Use connection pooling

## Data Recovery

### Re-process from MinIO
Raw payloads are stored in MinIO under `weather-data/raw/` by source and date.

### Re-run synthetic data
```bash
python -m cli.main generate --records 10000 --output data/replay/recovery.ndjson
python -m cli.main pipeline process --file data/replay/recovery.ndjson
```

### Reset database
```bash
docker compose exec postgres psql -U weather -d weatherdb -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose restart backend
```
