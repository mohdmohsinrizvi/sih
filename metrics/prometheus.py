from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server

RECORDS_RECEIVED = Counter("weather_records_received_total", "Total records received", ["source_type"])
RECORDS_PROCESSED = Counter("weather_records_processed_total", "Total records processed", ["stage", "status"])
RECORDS_FAILED = Counter("weather_records_failed_total", "Total records failed", ["stage", "error_type"])
RECORDS_QUARANTINED = Counter("weather_records_quarantined_total", "Total records quarantined", ["reason"])

RECORDS_PER_SECOND = Gauge("weather_records_per_second", "Current processing rate")
PROCESSING_LATENCY = Histogram("weather_processing_latency_seconds", "Processing latency", ["stage"], buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0])
QUEUE_LAG = Gauge("weather_queue_lag", "Queue lag", ["topic"])

DUPLICATE_CANDIDATES = Counter("weather_duplicate_candidates_total", "Duplicate candidates found", ["type"])
EVENTS_CREATED = Counter("weather_events_created_total", "Events created", ["category"])
SOURCE_HEALTH = Gauge("weather_source_health", "Source health status", ["source_id"])
API_FAILURE_RATE = Gauge("weather_api_failure_rate", "API failure rate", ["endpoint"])

PIPELINE_RECORDS = Gauge("weather_pipeline_records", "Pipeline record counts", ["metric"])

METRICS_PORT = 9090


def start_metrics_server(port: int = METRICS_PORT) -> None:
    try:
        start_http_server(port)
    except OSError:
        pass


def record_received(source_type: str) -> None:
    RECORDS_RECEIVED.labels(source_type=source_type).inc()


def record_processed(stage: str, status: str) -> None:
    RECORDS_PROCESSED.labels(stage=stage, status=status).inc()


def record_failed(stage: str, error_type: str) -> None:
    RECORDS_FAILED.labels(stage=stage, error_type=error_type).inc()


def record_quarantined(reason: str) -> None:
    RECORDS_QUARANTINED.labels(reason=reason).inc()


def update_pipeline_metrics(metrics: dict) -> None:
    PIPELINE_RECORDS.labels(metric="received").set(metrics.get("records_received", 0))
    PIPELINE_RECORDS.labels(metric="normalized").set(metrics.get("records_normalized", 0))
    PIPELINE_RECORDS.labels(metric="validated").set(metrics.get("records_validated", 0))
    PIPELINE_RECORDS.labels(metric="quarantined").set(metrics.get("records_quarantined", 0))
    PIPELINE_RECORDS.labels(metric="stored").set(metrics.get("records_stored", 0))
    PIPELINE_RECORDS.labels(metric="failed").set(metrics.get("records_failed", 0))
    RECORDS_PER_SECOND.set(metrics.get("records_per_second", 0))
