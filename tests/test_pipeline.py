"""
Integration tests for the full pipeline.
"""

import csv
from pathlib import Path

import pytest

from core.config import PipelineConfig, DATA_DIR, OUTPUTS_DIR
from core.orchestrator import PipelineOrchestrator


@pytest.fixture
def pipeline_config(tmp_path):
    """Create a config that uses the real data files but writes to tmp."""
    config = PipelineConfig()
    config.tickets_output_path = tmp_path / "generated_tickets.csv"
    config.processing_log_path = tmp_path / "processing_log.csv"
    config.metrics_output_path = tmp_path / "metrics.csv"
    return config


class TestPipelineIntegration:
    def test_full_pipeline_runs(self, pipeline_config):
        """Verify the entire pipeline executes without errors."""
        orchestrator = PipelineOrchestrator(pipeline_config)
        results = orchestrator.run()

        assert "tickets" in results
        assert "metrics" in results
        assert "processing_time" in results
        assert len(results["tickets"]) > 0
        assert results["processing_time"] > 0

    def test_pipeline_produces_output_files(self, pipeline_config):
        """Verify that all expected output CSVs are created."""
        orchestrator = PipelineOrchestrator(pipeline_config)
        orchestrator.run()

        assert pipeline_config.tickets_output_path.exists()
        assert pipeline_config.processing_log_path.exists()
        assert pipeline_config.metrics_output_path.exists()

    def test_tickets_have_required_fields(self, pipeline_config):
        """Verify generated tickets contain all required fields."""
        orchestrator = PipelineOrchestrator(pipeline_config)
        results = orchestrator.run()

        required = {
            "ticket_id", "title", "description", "category",
            "priority", "source_id", "source_type", "confidence",
        }
        for ticket in results["tickets"]:
            for field in required:
                assert field in ticket, f"Missing field: {field}"

    def test_metrics_contain_accuracy(self, pipeline_config):
        """Verify metrics include classification accuracy."""
        orchestrator = PipelineOrchestrator(pipeline_config)
        results = orchestrator.run()

        metrics = results["metrics"]
        assert "overall_accuracy" in metrics
        assert 0 <= metrics["overall_accuracy"] <= 1

    def test_all_records_processed(self, pipeline_config):
        """Verify all input records produce tickets."""
        orchestrator = PipelineOrchestrator(pipeline_config)
        results = orchestrator.run()

        # We have 30 reviews + 20 emails = 50 records
        assert len(results["tickets"]) == 50

    def test_categories_are_valid(self, pipeline_config):
        """Verify all tickets have valid categories."""
        valid_categories = {"Bug", "Feature Request", "Praise", "Complaint", "Spam", "Unknown"}
        orchestrator = PipelineOrchestrator(pipeline_config)
        results = orchestrator.run()

        for ticket in results["tickets"]:
            assert ticket["category"] in valid_categories, (
                f"Invalid category: {ticket['category']}"
            )

    def test_metrics_csv_format(self, pipeline_config):
        """Verify metrics CSV has correct format."""
        orchestrator = PipelineOrchestrator(pipeline_config)
        orchestrator.run()

        with open(pipeline_config.metrics_output_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) > 0
        assert "metric" in rows[0]
        assert "value" in rows[0]

    def test_pipeline_with_missing_expected_file(self, pipeline_config, tmp_path):
        """Pipeline should still work even if expected_classifications.csv is missing."""
        pipeline_config.expected_classifications_path = tmp_path / "nonexistent.csv"
        orchestrator = PipelineOrchestrator(pipeline_config)
        results = orchestrator.run()

        assert len(results["tickets"]) > 0
        assert results["metrics"]["overall_accuracy"] == 0.0
