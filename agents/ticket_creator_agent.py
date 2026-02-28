"""
Ticket Creator Agent — generates structured tickets from classified feedback.

Produces a ticket for each record with:
- ticket_id, title, description, category, priority,
  source_id, source_type, confidence, extracted_metadata
"""

import json
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from core.logger import ProcessingLogger
from core.utils import generate_ticket_id


class TicketCreatorAgent(BaseAgent):
    """Agent that creates structured tickets from processed feedback records."""

    def __init__(self, logger: ProcessingLogger):
        super().__init__("TicketCreatorAgent", logger)

    def execute(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate a ticket for each classified record."""
        self.log("create_tickets", "INFO", f"Creating tickets for {len(records)} records")
        tickets: List[Dict[str, Any]] = []

        for idx, record in enumerate(records, start=1):
            try:
                ticket = self._create_ticket(record, idx)
                tickets.append(ticket)
            except Exception as exc:
                self.log_error(
                    "create_ticket", str(exc),
                    record_id=record.get("record_id", ""),
                )

        self.log_success(
            "create_tickets",
            f"Generated {len(tickets)} tickets",
        )
        return tickets

    def _create_ticket(self, record: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Build a single ticket dict from a processed record."""
        category = record.get("category", "Unknown")
        ticket_id = generate_ticket_id(index, category)
        title = self._generate_title(record)
        description = self._generate_description(record)
        priority = record.get("priority", "Medium")

        # Gather extracted metadata
        extracted_metadata = {}
        if "bug_details" in record:
            extracted_metadata["bug_details"] = record["bug_details"]
        if "feature_details" in record:
            extracted_metadata["feature_details"] = record["feature_details"]

        ticket = {
            "ticket_id": ticket_id,
            "title": title,
            "description": description,
            "category": category,
            "priority": priority,
            "source_id": record.get("record_id", ""),
            "source_type": record.get("source_type", ""),
            "confidence": record.get("confidence", 0.0),
            "extracted_metadata": json.dumps(extracted_metadata),
        }

        self.log_success(
            "create_ticket",
            f"Created {ticket_id}: {title[:50]}",
            record_id=record.get("record_id", ""),
        )
        return ticket

    @staticmethod
    def _generate_title(record: Dict[str, Any]) -> str:
        """Generate a concise ticket title based on category and content."""
        category = record.get("category", "Feedback")
        text = record.get("text", "")

        if category == "Bug":
            bug_details = record.get("bug_details", {})
            severity = bug_details.get("severity", "")
            # Use first sentence as title basis
            first_sentence = text.split(".")[0].strip()
            if len(first_sentence) > 80:
                first_sentence = first_sentence[:77] + "..."
            prefix = f"[{severity}] " if severity else ""
            return f"{prefix}{first_sentence}"

        elif category == "Feature Request":
            feature_details = record.get("feature_details", {})
            theme = feature_details.get("theme", "")
            desc = feature_details.get("description", "")
            if theme and theme != "other":
                return f"Feature Request: {theme.title()}"
            if desc:
                short = desc[:70] + "..." if len(desc) > 70 else desc
                return f"Feature Request: {short}"
            return "Feature Request: User suggestion"

        elif category == "Praise":
            return "Positive Feedback: User satisfaction report"

        elif category == "Complaint":
            first_sentence = text.split(".")[0].strip()
            if len(first_sentence) > 80:
                first_sentence = first_sentence[:77] + "..."
            return f"Complaint: {first_sentence}"

        elif category == "Spam":
            return "Spam: Flagged content"

        return f"{category}: {text[:60]}..."

    @staticmethod
    def _generate_description(record: Dict[str, Any]) -> str:
        """Generate a structured ticket description."""
        parts = [record.get("text", "")]

        if "bug_details" in record:
            bd = record["bug_details"]
            parts.append(
                f"\n--- Bug Details ---\n"
                f"Device: {bd.get('device', 'N/A')}\n"
                f"OS: {bd.get('os', 'N/A')}\n"
                f"App Version: {bd.get('app_version', 'N/A')}\n"
                f"Severity: {bd.get('severity', 'N/A')}\n"
                f"Repro Steps: {bd.get('reproduction_steps', 'N/A')}"
            )

        if "feature_details" in record:
            fd = record["feature_details"]
            parts.append(
                f"\n--- Feature Details ---\n"
                f"Theme: {fd.get('theme', 'N/A')}\n"
                f"Demand Score: {fd.get('demand_score', 'N/A')}\n"
                f"Occurrences: {fd.get('occurrences', 'N/A')}"
            )

        return "\n".join(parts)
