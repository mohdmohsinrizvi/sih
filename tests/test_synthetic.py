import pytest
import os
from synthetic.generator import SyntheticWeatherGenerator, SyntheticConfig


class TestSyntheticGenerator:
    def test_generate_records(self):
        config = SyntheticConfig(total_records=100, seed=42, batch_size=10)
        generator = SyntheticWeatherGenerator(config)

        count = 0
        for report in generator.generate():
            count += 1
            assert "report_id" in report
            assert "source_id" in report
            assert "event_category" in report
            assert "timestamp" in report
            assert report["is_simulated"] is True
            if count >= 100:
                break

        assert count >= 90  # Allow small variance from integer division in cluster generation

    def test_generate_to_file(self, tmp_path):
        filepath = str(tmp_path / "test_output.ndjson")
        config = SyntheticConfig(total_records=50, seed=42)
        generator = SyntheticWeatherGenerator(config)
        generator.generate_to_file(filepath, 50)

        assert os.path.exists(filepath)

        with open(filepath, "r") as f:
            lines = f.readlines()
            assert len(lines) >= 45  # Allow small variance from integer division

    def test_generate_batches(self):
        config = SyntheticConfig(total_records=25, seed=42, batch_size=10)
        generator = SyntheticWeatherGenerator(config)

        total = 0
        for batch in generator.generate_batches():
            assert len(batch) <= 10
            total += len(batch)
            if total >= 25:
                break

        assert total > 0

    def test_event_distribution(self):
        config = SyntheticConfig(total_records=1000, seed=42)
        generator = SyntheticWeatherGenerator(config)

        categories = {}
        for report in generator.generate():
            cat = report["event_category"]
            categories[cat] = categories.get(cat, 0) + 1

        assert len(categories) > 1
        assert "rainfall" in categories

    def test_duplicates_generated(self):
        config = SyntheticConfig(
            total_records=200,
            duplicate_ratio=0.3,
            near_duplicate_ratio=0.2,
            seed=42,
        )
        generator = SyntheticWeatherGenerator(config)

        exact_dups = 0
        near_dups = 0
        originals = 0

        for report in generator.generate():
            dup_type = report.get("extra_metadata", {}).get("duplicate_type")
            if dup_type == "exact":
                exact_dups += 1
            elif dup_type == "near_duplicate":
                near_dups += 1
            else:
                originals += 1

        assert exact_dups > 0
        assert near_dups > 0

    def test_all_reports_have_is_simulated(self):
        config = SyntheticConfig(total_records=100, seed=42)
        generator = SyntheticWeatherGenerator(config)

        for report in generator.generate():
            assert report["is_simulated"] is True

    def test_geographic_coverage(self):
        config = SyntheticConfig(total_records=500, seed=42)
        generator = SyntheticWeatherGenerator(config)

        cities = set()
        for report in generator.generate():
            cities.add(report["city"])

        assert len(cities) > 10
