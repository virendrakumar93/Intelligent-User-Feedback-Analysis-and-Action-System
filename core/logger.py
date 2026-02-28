"""
Logging module for the Intelligent Feedback Analysis System.

Provides structured logging with both console output and CSV processing log.
"""

import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core.config import OUTPUTS_DIR


class ProcessingLogger:
    """Handles structured logging to processing_log.csv and console."""

    LOG_FIELDS = [
        "timestamp", "agent", "action", "record_id",
        "status", "message", "details",
    ]

    def __init__(self, log_path: Optional[Path] = None, level: str = "INFO"):
        self.log_path = log_path or OUTPUTS_DIR / "processing_log.csv"
        self._ensure_log_file()
        self._setup_console_logger(level)

    def _ensure_log_file(self) -> None:
        """Create log file with header if it doesn't exist."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.LOG_FIELDS)
                writer.writeheader()

    def _setup_console_logger(self, level: str) -> None:
        """Configure Python logger for console output."""
        self.console_logger = logging.getLogger("feedback_system")
        self.console_logger.setLevel(getattr(logging, level, logging.INFO))
        if not self.console_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self.console_logger.addHandler(handler)

    def log(
        self,
        agent: str,
        action: str,
        status: str,
        message: str,
        record_id: str = "",
        details: str = "",
    ) -> None:
        """Write a structured log entry to both CSV and console."""
        timestamp = datetime.now(timezone.utc).isoformat()
        row = {
            "timestamp": timestamp,
            "agent": agent,
            "action": action,
            "record_id": record_id,
            "status": status,
            "message": message,
            "details": details,
        }
        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.LOG_FIELDS)
            writer.writerow(row)

        log_msg = f"[{agent}] {action}: {message}"
        if status == "ERROR":
            self.console_logger.error(log_msg)
        elif status == "WARNING":
            self.console_logger.warning(log_msg)
        else:
            self.console_logger.info(log_msg)

    def log_error(
        self, agent: str, action: str, message: str,
        record_id: str = "", details: str = "",
    ) -> None:
        """Convenience method for error logging."""
        self.log(agent, action, "ERROR", message, record_id, details)

    def log_success(
        self, agent: str, action: str, message: str,
        record_id: str = "", details: str = "",
    ) -> None:
        """Convenience method for success logging."""
        self.log(agent, action, "SUCCESS", message, record_id, details)

    def reset(self) -> None:
        """Clear the log file and recreate header."""
        with open(self.log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.LOG_FIELDS)
            writer.writeheader()
