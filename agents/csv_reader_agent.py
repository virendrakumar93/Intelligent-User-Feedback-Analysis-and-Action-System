"""
CSV Reader Agent — reads and validates input CSV files.

Responsibilities:
- Read app_store_reviews.csv and support_emails.csv
- Validate schema and required columns
- Handle missing values gracefully
- Standardize timestamps
- Log ingestion metadata
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from core.logger import ProcessingLogger
from core.utils import parse_timestamp, read_csv_safe, sanitize_text


# Expected schemas for each source type
REVIEW_REQUIRED_COLUMNS = {"review_id", "review_text"}
EMAIL_REQUIRED_COLUMNS = {"email_id", "body"}


class CSVReaderAgent(BaseAgent):
    """Agent that ingests and validates CSV feedback data."""

    def __init__(self, logger: ProcessingLogger):
        super().__init__("CSVReaderAgent", logger)

    def execute(
        self,
        reviews_path: Optional[Path] = None,
        emails_path: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """Read and merge feedback from both CSV sources.

        Returns a unified list of feedback records with standardized fields:
            record_id, source_type, text, date, metadata
        """
        records: List[Dict[str, Any]] = []

        if reviews_path and reviews_path.exists():
            records.extend(self._read_reviews(reviews_path))

        if emails_path and emails_path.exists():
            records.extend(self._read_emails(emails_path))

        if not records:
            self.log_error("ingest", "No records found in any input file")
            return records

        self.log_success(
            "ingest",
            f"Total records ingested: {len(records)}",
            details=f"reviews={sum(1 for r in records if r['source_type']=='app_review')}, "
                    f"emails={sum(1 for r in records if r['source_type']=='support_email')}",
        )
        return records

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _read_reviews(self, path: Path) -> List[Dict[str, Any]]:
        """Parse app_store_reviews.csv into unified records."""
        self.log("read_reviews", "INFO", f"Reading {path}")
        try:
            rows = read_csv_safe(path)
        except FileNotFoundError as exc:
            self.log_error("read_reviews", str(exc))
            return []

        if not self._validate_schema(rows, REVIEW_REQUIRED_COLUMNS, "reviews"):
            return []

        records: List[Dict[str, Any]] = []
        for row in rows:
            record = {
                "record_id": row.get("review_id", ""),
                "source_type": "app_review",
                "text": sanitize_text(row.get("review_text", "")),
                "date": parse_timestamp(row.get("date", "")),
                "metadata": {
                    "user_name": row.get("user_name", ""),
                    "rating": row.get("rating", ""),
                    "app_version": row.get("app_version", ""),
                    "device": row.get("device", ""),
                },
            }
            if not record["text"]:
                self.log(
                    "read_reviews", "WARNING",
                    "Empty review text, skipping",
                    record_id=record["record_id"],
                )
                continue
            records.append(record)

        self.log_success(
            "read_reviews",
            f"Parsed {len(records)} reviews from {path.name}",
        )
        return records

    def _read_emails(self, path: Path) -> List[Dict[str, Any]]:
        """Parse support_emails.csv into unified records."""
        self.log("read_emails", "INFO", f"Reading {path}")
        try:
            rows = read_csv_safe(path)
        except FileNotFoundError as exc:
            self.log_error("read_emails", str(exc))
            return []

        if not self._validate_schema(rows, EMAIL_REQUIRED_COLUMNS, "emails"):
            return []

        records: List[Dict[str, Any]] = []
        for row in rows:
            body = sanitize_text(row.get("body", ""))
            subject = sanitize_text(row.get("subject", ""))
            combined_text = f"{subject}. {body}" if subject else body

            record = {
                "record_id": row.get("email_id", ""),
                "source_type": "support_email",
                "text": combined_text,
                "date": parse_timestamp(row.get("date", "")),
                "metadata": {
                    "sender": row.get("sender", ""),
                    "subject": subject,
                    "priority_stated": row.get("priority_stated", ""),
                },
            }
            if not record["text"]:
                self.log(
                    "read_emails", "WARNING",
                    "Empty email body, skipping",
                    record_id=record["record_id"],
                )
                continue
            records.append(record)

        self.log_success(
            "read_emails",
            f"Parsed {len(records)} emails from {path.name}",
        )
        return records

    def _validate_schema(
        self, rows: List[Dict[str, Any]], required: set, label: str
    ) -> bool:
        """Check that required columns exist in the CSV data."""
        if not rows:
            self.log_error("validate_schema", f"No rows found in {label} CSV")
            return False
        actual_cols = set(rows[0].keys())
        missing = required - actual_cols
        if missing:
            self.log_error(
                "validate_schema",
                f"Missing columns in {label}: {missing}",
            )
            return False
        return True
