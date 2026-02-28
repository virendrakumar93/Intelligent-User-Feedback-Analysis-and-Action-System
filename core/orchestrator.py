"""
Pipeline Orchestrator — coordinates all agents in sequence.

Execution order:
1. CSVReaderAgent    — ingest and validate data
2. ClassifierAgent   — classify feedback
3. BugAnalysisAgent  — enrich bug reports
4. FeatureExtractorAgent — analyze feature requests
5. TicketCreatorAgent — generate tickets
6. QualityCriticAgent — quality review
7. Metrics computation
"""

import time
from typing import Any, Dict, List

from agents.bug_analysis_agent import BugAnalysisAgent
from agents.classifier_agent import ClassifierAgent
from agents.csv_reader_agent import CSVReaderAgent
from agents.feature_extractor_agent import FeatureExtractorAgent
from agents.quality_critic_agent import QualityCriticAgent
from agents.ticket_creator_agent import TicketCreatorAgent
from core.config import PipelineConfig
from core.logger import ProcessingLogger
from core.metrics import compute_metrics, save_metrics_csv
from core.utils import write_csv


TICKET_FIELDS = [
    "ticket_id", "title", "description", "category", "priority",
    "source_id", "source_type", "confidence", "extracted_metadata",
    "quality_issues", "quality_passed",
]


class PipelineOrchestrator:
    """Orchestrates the multi-agent feedback analysis pipeline."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.logger = ProcessingLogger(
            log_path=config.processing_log_path,
            level=config.log_level,
        )
        # Initialize agents
        self.csv_reader = CSVReaderAgent(self.logger)
        self.classifier = ClassifierAgent(self.logger, config.classification)
        self.bug_analyzer = BugAnalysisAgent(self.logger, config.priority)
        self.feature_extractor = FeatureExtractorAgent(self.logger, config.priority)
        self.ticket_creator = TicketCreatorAgent(self.logger)
        self.quality_critic = QualityCriticAgent(
            self.logger, config.classification.confidence_threshold
        )

    def run(self) -> Dict[str, Any]:
        """Execute the full pipeline and return results summary.

        Returns:
            Dict with keys: tickets, metrics, processing_time
        """
        self.logger.reset()
        self.logger.log(
            "Orchestrator", "pipeline_start", "INFO",
            "Starting feedback analysis pipeline",
        )
        start_time = time.time()

        # Step 1: Ingest data
        records = self.csv_reader.execute(
            reviews_path=self.config.app_reviews_path,
            emails_path=self.config.support_emails_path,
        )
        if not records:
            self.logger.log_error(
                "Orchestrator", "pipeline_abort",
                "No records ingested — aborting pipeline",
            )
            return {"tickets": [], "metrics": {}, "processing_time": 0.0}

        # Step 2: Classify
        records = self.classifier.execute(records)

        # Step 3: Analyze bugs
        records = self.bug_analyzer.execute(records)

        # Step 4: Extract features
        records = self.feature_extractor.execute(records)

        # Step 5: Assign default priority to non-bug/non-feature records
        for r in records:
            if "priority" not in r:
                cat = r.get("category", "")
                if cat == "Praise":
                    r["priority"] = "Low"
                elif cat == "Complaint":
                    r["priority"] = "High"
                elif cat == "Spam":
                    r["priority"] = "Low"
                else:
                    r["priority"] = "Medium"

        # Step 6: Create tickets
        tickets = self.ticket_creator.execute(records)

        # Step 7: Quality review
        tickets = self.quality_critic.execute(tickets)

        processing_time = time.time() - start_time

        # Step 8: Compute metrics
        metrics = compute_metrics(
            tickets,
            self.config.expected_classifications_path,
            processing_time,
        )

        # Step 9: Save outputs
        self._save_outputs(tickets, metrics)

        self.logger.log(
            "Orchestrator", "pipeline_complete", "SUCCESS",
            f"Pipeline completed in {processing_time:.2f}s — "
            f"{len(tickets)} tickets generated, "
            f"accuracy={metrics.get('overall_accuracy', 0):.2%}",
        )

        return {
            "tickets": tickets,
            "metrics": metrics,
            "processing_time": processing_time,
        }

    def _save_outputs(
        self, tickets: List[Dict[str, Any]], metrics: Dict[str, Any]
    ) -> None:
        """Persist tickets and metrics to CSV files."""
        # Convert quality_issues list to string for CSV
        export_rows = []
        for t in tickets:
            row = {k: t.get(k, "") for k in TICKET_FIELDS}
            if isinstance(row.get("quality_issues"), list):
                row["quality_issues"] = "; ".join(row["quality_issues"])
            export_rows.append(row)

        write_csv(self.config.tickets_output_path, export_rows, TICKET_FIELDS)
        save_metrics_csv(metrics, self.config.metrics_output_path)
