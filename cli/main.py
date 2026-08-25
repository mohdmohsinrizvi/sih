from __future__ import annotations

import asyncio
import json
import sys

import click
import structlog

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

logger = structlog.get_logger(__name__)
console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """National Weather Big Data Analytics Platform CLI"""
    pass


@cli.group()
def ingest():
    """Ingestion commands"""
    pass


@ingest.command("start")
@click.option("--source", default="synthetic", help="Source to ingest from")
@click.option("--records", default=1000, help="Number of records")
def ingest_start(source, records):
    """Start ingestion from a source"""
    from synthetic.generator import SyntheticWeatherGenerator, SyntheticConfig

    console.print(f"[bold green]Starting ingestion from {source}...[/bold green]")

    config = SyntheticConfig(total_records=records, batch_size=100)
    generator = SyntheticWeatherGenerator(config)

    count = 0
    for report in generator.generate():
        count += 1
        if count % 1000 == 0:
            console.print(f"  Generated {count} records...")

    console.print(f"[bold green]Ingestion complete: {count} records[/bold green]")


@ingest.command("stop")
def ingest_stop():
    """Stop active ingestion"""
    console.print("[bold yellow]Ingestion stop requested[/bold yellow]")


@cli.group()
def source():
    """Source management commands"""
    pass


@source.command("list")
def source_list():
    """List all registered sources"""
    from connectors.registry import registry

    table = Table(title="Registered Sources")
    table.add_column("Source ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Enabled", style="blue")
    table.add_column("Health", style="magenta")

    for s in registry.list_all():
        table.add_row(
            s.source_id,
            s.source_name,
            s.source_type,
            "Yes" if s.enabled else "No",
            s.health_status,
        )

    console.print(table)


@source.command("health")
def source_health():
    """Check source health"""
    from connectors.registry import registry

    sources = registry.list_all()
    console.print(f"Total sources: {len(sources)}")
    for s in sources:
        status = "✓" if s.health_status == "healthy" else "?"
        console.print(f"  {status} {s.source_id}: {s.health_status}")


@cli.command("generate")
@click.option("--records", default=10000, help="Number of records to generate")
@click.option("--output", default="data/replay/synthetic.ndjson", help="Output file")
@click.option("--seed", default=42, help="Random seed")
def generate(records, output, seed):
    """Generate synthetic weather data"""
    from synthetic.generator import SyntheticWeatherGenerator, SyntheticConfig

    console.print(f"[bold cyan]Generating {records} synthetic records...[/bold cyan]")

    config = SyntheticConfig(total_records=records, seed=seed, batch_size=1000)
    generator = SyntheticWeatherGenerator(config)
    generator.generate_to_file(output, records)

    console.print(f"[bold green]Generated {records} records → {output}[/bold green]")


@cli.group()
def replay_cmd():
    """Replay commands"""
    pass


@replay_cmd.command("start")
@click.option("--file", required=True, help="Replay file path")
@click.option("--speed", default=1, help="Replay speed multiplier")
@click.option("--topic", default="weather.raw", help="Target topic")
def replay_start(file, speed, topic):
    """Start replaying data"""
    from replay_engine.engine import replay as replay_engine

    console.print(f"[bold cyan]Starting replay at {speed}x speed...[/bold cyan]")
    asyncio.run(replay_engine.start(file, topic, speed))


@replay_cmd.command("status")
def replay_status():
    """Show replay status"""
    from replay_engine.engine import replay as replay_engine

    stats = replay_engine.stats.to_dict()
    table = Table(title="Replay Status")
    for key, value in stats.items():
        table.add_row(key, str(value))
    console.print(table)


@cli.group()
def pipeline_grp():
    """Pipeline commands"""
    pass


@pipeline_grp.command("status")
def pipeline_status():
    """Show pipeline status"""
    console.print("[bold cyan]Pipeline Status[/bold cyan]")
    console.print("Use GET /pipeline/status API endpoint for live status")


@pipeline_grp.command("process")
@click.option("--file", required=True, help="NDJSON file to process")
@click.option("--batch-size", default=100, help="Batch size")
def pipeline_process(file, batch_size):
    """Process a file through the pipeline"""
    from pipeline.processor import pipeline as weather_pipeline

    console.print(f"[bold cyan]Processing {file}...[/bold cyan]")

    async def _process():
        import orjson
        batch = []
        with open(file, "rb") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = orjson.loads(line)
                    batch.append(data)
                    if len(batch) >= batch_size:
                        metrics = await weather_pipeline.process_batch(batch)
                        console.print(f"  Processed batch of {len(batch)}: {metrics.to_dict()}")
                        batch = []
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")

        if batch:
            metrics = await weather_pipeline.process_batch(batch)
            console.print(f"  Processed final batch of {len(batch)}: {metrics.to_dict()}")

    asyncio.run(_process())


@cli.command("data-quality")
def data_quality():
    """Show data quality report"""
    console.print("[bold cyan]Data Quality Report[/bold cyan]")
    console.print("Use GET /data-quality API endpoint for detailed report")


@cli.command("dedup-stats")
def dedup_stats():
    """Show deduplication statistics"""
    console.print("[bold cyan]Deduplication Statistics[/bold cyan]")
    console.print("Use GET /pipeline/status for dedup metrics")


@cli.command("test")
def run_tests():
    """Run test suite"""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        capture_output=False,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    cli()
