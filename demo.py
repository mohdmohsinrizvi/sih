#!/usr/bin/env python3
"""Ek command me sab test karo — python demo.py"""

import asyncio
import subprocess
import sys
import os
import json
import time
from pathlib import Path

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def banner(text, color=CYAN):
    line = "=" * 60
    print(f"\n{color}{line}")
    print(f"  {text}")
    print(f"{line}{RESET}\n")

def step(num, text):
    print(f"{BOLD}{CYAN}[Step {num}]{RESET} {text}")

def ok(text):
    print(f"  {GREEN}✓{RESET} {text}")

def warn(text):
    print(f"  {YELLOW}⚠{RESET} {text}")

def fail(text):
    print(f"  {RED}✗{RESET} {text}")

def info(label, value):
    print(f"  {CYAN}{label}:{RESET} {value}")


def check_docker():
    step(1, "Checking Docker services...")
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n")
    required = {"weather-postgres", "weather-redpanda", "weather-redis", "weather-minio"}
    running = set()
    for line in lines:
        parts = line.split("\t")
        if len(parts) >= 2:
            running.add(parts[0])
            status = parts[1]
            if "healthy" in status.lower():
                ok(f"{parts[0]} — {status}")
            else:
                warn(f"{parts[0]} — {status}")

    missing = required - running
    if missing:
        fail(f"Missing services: {', '.join(missing)}")
        print(f"\n  {YELLOW}Run: docker-compose up -d{RESET}")
        return False
    ok("All 4 services running!")
    return True


def check_api():
    step(2, "Checking Backend API...")
    import httpx
    try:
        r = httpx.get("http://localhost:8000/health", timeout=3)
        if r.status_code == 200:
            ok("Backend API is healthy!")
            return True
    except Exception:
        pass

    fail("Backend API not running!")
    print(f"\n  {YELLOW}Starting backend...{RESET}")
    subprocess.run(
        ["screen", "-S", "backend", "-X", "quit"],
        capture_output=True
    )
    time.sleep(1)
    subprocess.Popen(
        ["screen", "-dmS", "backend", "bash", "-c",
         f"cd {os.getcwd()} && .venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(5)
    try:
        r = httpx.get("http://localhost:8000/health", timeout=3)
        if r.status_code == 200:
            ok("Backend API started successfully!")
            return True
    except Exception:
        pass
    fail("Could not start backend. Check: cat /tmp/backend.log")
    return False


def seed_sources():
    step(3, "Seeding synthetic sources into database...")
    sources = ["synthetic_api", "synthetic_social", "synthetic_web", "synthetic_citizen"]
    values = ", ".join(
        f"('{s}', 'Synthetic {s.split('_')[1].title()} Source', 'api', 'synthetic', true, 1.0, 'India', 'healthy', '{{}}', NOW(), NOW())"
        for s in sources
    )
    sql = f"""INSERT INTO sources (source_id, source_name, source_type, connector_type, enabled, reliability, geographic_coverage, health_status, extra_metadata, created_at, updated_at)
    VALUES {values} ON CONFLICT (source_id) DO NOTHING;"""

    result = subprocess.run(
        ["docker", "exec", "weather-postgres", "psql", "-U", "weather", "-d", "weatherdb", "-c", sql],
        capture_output=True, text=True
    )
    if "INSERT" in result.stdout:
        ok(f"Inserted {len(sources)} synthetic sources")
    else:
        ok("Sources already exist")
    return True


def generate_data():
    step(4, "Generating 1000 synthetic weather records...")
    from synthetic.generator import SyntheticWeatherGenerator, SyntheticConfig

    config = SyntheticConfig(total_records=1000, seed=42, batch_size=1000)
    gen = SyntheticWeatherGenerator(config)
    gen.generate_to_file("data/replay/synthetic.ndjson", 1000)

    count = sum(1 for _ in open("data/replay/synthetic.ndjson"))
    ok(f"Generated {count} records → data/replay/synthetic.ndjson")
    return True


def process_pipeline():
    step(5, "Processing records through pipeline...")
    from pipeline.processor import pipeline
    from connectors.base import RawPayload

    async def run():
        batch = []
        with open("data/replay/synthetic.ndjson", "rb") as f:
            for line in f:
                if line.strip():
                    batch.append(json.loads(line.strip()))

        metrics = await pipeline.process_batch(batch)
        return metrics.to_dict()

    result = asyncio.run(run())
    ok(f"Records received:   {result['records_received']}")
    ok(f"Records stored:     {result['records_stored']}")
    ok(f"Records failed:     {result['records_failed']}")
    ok(f"Dedup candidates:   {result['duplicate_candidates']}")
    ok(f"Event candidates:   {result['event_candidates']}")
    ok(f"Speed:              {result['records_per_second']} records/sec")
    return result


def show_results():
    step(6, "Fetching results from API...")
    import httpx

    try:
        stats = httpx.get("http://localhost:8000/stats/summary", timeout=5).json()
        info("Total Reports", stats.get("total_reports", 0))
        info("Total Events", stats.get("total_events", 0))
        info("Total Sources", stats.get("total_sources", 0))
    except Exception:
        warn("Could not fetch stats (API may need restart)")

    print()
    try:
        quality = httpx.get("http://localhost:8000/data-quality", timeout=5).json()
        total = quality.get("total_records", 0)
        valid = quality.get("valid", 0)
        info("Data Quality", f"{valid}/{total} valid ({valid*100//total if total else 0}%)")
    except Exception:
        pass

    print()
    try:
        reports = httpx.get("http://localhost:8000/reports?limit=5", timeout=5).json()
        print(f"  {BOLD}Sample Reports:{RESET}")
        for r in reports.get("reports", []):
            city = r.get("city", "?")
            state = r.get("state", "?")
            cat = r.get("event_category", "?")
            sev = r.get("severity", "?")
            print(f"    • {city}, {state} — {cat} (severity: {sev})")
    except Exception:
        pass

    return True


def show_api_endpoints():
    step(7, "Available API Endpoints (test in browser or curl):")
    endpoints = [
        ("GET", "/", "Platform info"),
        ("GET", "/health", "Health check"),
        ("GET", "/docs", "Swagger UI (browser)"),
        ("GET", "/reports?limit=10", "List reports"),
        ("GET", "/reports/{id}", "Single report"),
        ("GET", "/events/candidates", "Weather events"),
        ("GET", "/data-quality", "Quality report"),
        ("GET", "/stats/summary", "Statistics"),
        ("GET", "/sources", "All sources"),
        ("GET", "/sources/health", "Source health"),
        ("GET", "/ingestion/status", "Pipeline status"),
    ]
    for method, path, desc in endpoints:
        print(f"    {GREEN}{method:4}{RESET} {CYAN}{path:30}{RESET} {desc}")


def main():
    banner("🌦️  NATIONAL WEATHER PLATFORM — FULL DEMO", CYAN)

    if not check_docker():
        sys.exit(1)

    if not check_api():
        sys.exit(1)

    seed_sources()
    generate_data()
    result = process_pipeline()
    show_results()
    show_api_endpoints()

    banner("🎉  DEMO COMPLETE!", GREEN)
    print(f"  {BOLD}Swagger UI:{RESET} http://localhost:8000/docs")
    print(f"  {BOLD}Reports:{RESET}    http://localhost:8000/reports")
    print(f"  {BOLD}Quality:{RESET}    http://localhost:8000/data-quality")
    print(f"  {BOLD}Events:{RESET}     http://localhost:8000/events/candidates")
    print()


if __name__ == "__main__":
    main()
