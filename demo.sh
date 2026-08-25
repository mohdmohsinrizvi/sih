#!/bin/bash
set -e

echo "=============================================="
echo "  National Weather Big Data Analytics Platform"
echo "  SIH Problem Statement 26069 - Demo"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err() { echo -e "${RED}[ERROR]${NC} $1"; }

# Step 1: Verify Docker
log_info "Step 1: Verifying Docker installation..."
if ! command -v docker &> /dev/null; then
    log_err "Docker is not installed. Please install Docker first."
    exit 1
fi
if ! docker compose version &> /dev/null; then
    log_err "Docker Compose is not available."
    exit 1
fi
log_ok "Docker is available"

# Step 2: Start services
log_info "Step 2: Starting services via Docker Compose..."
docker compose up -d postgres redpanda redis minio
log_ok "Infrastructure services started"

# Wait for health checks
log_info "Waiting for services to be healthy..."
sleep 10

# Step 3: Check service health
log_info "Step 3: Checking service health..."
if docker compose ps postgres | grep -q "healthy"; then
    log_ok "PostgreSQL is healthy"
else
    log_warn "PostgreSQL may not be fully ready, continuing..."
fi

if docker compose ps redpanda | grep -q "healthy"; then
    log_ok "Redpanda is healthy"
else
    log_warn "Redpanda may not be fully ready, continuing..."
fi

if docker compose ps redis | grep -q "healthy"; then
    log_ok "Redis is healthy"
else
    log_warn "Redis may not be fully ready, continuing..."
fi

# Step 4: Generate synthetic data
log_info "Step 4: Generating synthetic weather data..."
python -m cli.main generate --records 10000 --output data/replay/synthetic.ndjson --seed 42
log_ok "Generated 10,000 synthetic weather records"

# Step 5: Start backend
log_info "Step 5: Starting backend API..."
docker compose up -d backend
sleep 5
log_ok "Backend API started at http://localhost:8000"

# Step 6: Process data through pipeline
log_info "Step 6: Processing data through pipeline..."
python -m cli.main pipeline process --file data/replay/synthetic.ndjson --batch-size 500
log_ok "Data processing complete"

# Step 7: Verify API endpoints
log_info "Step 7: Verifying API endpoints..."
API_URL="http://localhost:8000"

echo ""
echo "  API Health:"
curl -s "$API_URL/health" | python -m json.tool 2>/dev/null || echo "  (API not reachable via curl)"

echo ""
echo "  Sources:"
curl -s "$API_URL/sources" | python -m json.tool 2>/dev/null | head -20 || echo "  (API not reachable)"

echo ""
echo "  Reports count:"
curl -s "$API_URL/stats/summary" | python -m json.tool 2>/dev/null || echo "  (API not reachable)"

# Step 8: Show demo summary
echo ""
echo "=============================================="
echo "  Demo Complete!"
echo "=============================================="
echo ""
echo "  Services running:"
echo "    - PostgreSQL:  localhost:5432"
echo "    - Redpanda:    localhost:19092"
echo "    - Redis:       localhost:6379"
echo "    - MinIO:       localhost:9000 (console: localhost:9001)"
echo "    - Backend API: localhost:8000"
echo "    - API Docs:    http://localhost:8000/docs"
echo ""
echo "  Data:"
echo "    - Synthetic:   data/replay/synthetic.ndjson"
echo "    - Records:     10,000"
echo "    - Categories:  rainfall, flood, thunderstorm, heatwave, etc."
echo "    - Events:      Lucknow flood, Delhi heatwave, Mumbai rainfall, etc."
echo ""
echo "  Key features demonstrated:"
echo "    [x] Multiple sources (synthetic)"
echo "    [x] Real-time ingestion"
echo "    [x] Normalization"
echo "    [x] Validation"
echo "    [x] H3 geospatial indexing"
echo "    [x] Deduplication candidates"
echo "    [x] Event fusion candidates"
echo "    [x] Centralized storage"
echo ""
echo "  Run tests:  python -m pytest tests/ -v"
echo "  Stop:       docker compose down"
echo "=============================================="
