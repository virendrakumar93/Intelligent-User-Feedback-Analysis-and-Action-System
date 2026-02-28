"""
Base agent class providing shared interface and logging for all agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from core.logger import ProcessingLogger


class BaseAgent(ABC):
    """Abstract base class for all pipeline agents."""

    def __init__(self, name: str, logger: ProcessingLogger):
        self.name = name
        self.logger = logger

    @abstractmethod
    def execute(self, data: Any) -> Any:
        """Execute the agent's primary task."""

    def log(self, action: str, status: str, message: str,
            record_id: str = "", details: str = "") -> None:
        """Convenience wrapper for structured logging."""
        self.logger.log(self.name, action, status, message, record_id, details)

    def log_error(self, action: str, message: str,
                  record_id: str = "", details: str = "") -> None:
        self.logger.log_error(self.name, action, message, record_id, details)

    def log_success(self, action: str, message: str,
                    record_id: str = "", details: str = "") -> None:
        self.logger.log_success(self.name, action, message, record_id, details)
