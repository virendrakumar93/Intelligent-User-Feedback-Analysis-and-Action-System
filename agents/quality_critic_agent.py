"""
Quality Critic Agent — validates generated tickets for quality.

Checks:
- Title clarity (not empty, reasonable length)
- Priority consistency with category
- Missing fields
- Confidence threshold
- Flags low-confidence or problematic tickets
"""

from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from core.logger import ProcessingLogger


# Acceptable priority levels per category
EXPECTED_PRIORITIES = {
    "Bug": {"Critical", "High", "Medium"},
    "Feature Request": {"High", "Medium", "Low"},
    "Praise": {"Low"},
    "Complaint": {"High", "Medium"},
    "Spam": {"Low"},
}

REQUIRED_TICKET_FIELDS = [
    "ticket_id", "title", "description", "category",
    "priority", "source_id", "source_type", "confidence",
]


class QualityCriticAgent(BaseAgent):
    """Agent that reviews tickets for quality and flags issues."""

    def __init__(self, logger: ProcessingLogger, confidence_threshold: float = 0.6):
        super().__init__("QualityCriticAgent", logger)
        self.confidence_threshold = confidence_threshold

    def execute(self, tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate all tickets and attach quality review results."""
        self.log("review", "INFO", f"Reviewing {len(tickets)} tickets")
        flagged_count = 0

        for ticket in tickets:
            issues = self._review_ticket(ticket)
            ticket["quality_issues"] = issues
            ticket["quality_passed"] = len(issues) == 0
            if issues:
                flagged_count += 1
                self.log(
                    "review", "WARNING",
                    f"Issues found: {issues}",
                    record_id=ticket.get("ticket_id", ""),
                )
            else:
                self.log_success(
                    "review",
                    "Ticket passed quality check",
                    record_id=ticket.get("ticket_id", ""),
                )

        self.log_success(
            "summary",
            f"Review complete: {len(tickets) - flagged_count} passed, {flagged_count} flagged",
        )
        return tickets

    def _review_ticket(self, ticket: Dict[str, Any]) -> List[str]:
        """Run all quality checks on a single ticket."""
        issues: List[str] = []

        # 1. Check required fields
        for field in REQUIRED_TICKET_FIELDS:
            val = ticket.get(field)
            if val is None or (isinstance(val, str) and not val.strip()):
                issues.append(f"Missing field: {field}")

        # 2. Check title clarity
        title = ticket.get("title", "")
        if len(title) < 5:
            issues.append("Title too short")
        if len(title) > 200:
            issues.append("Title too long")

        # 3. Check confidence threshold
        confidence = ticket.get("confidence", 0.0)
        if isinstance(confidence, (int, float)) and confidence < self.confidence_threshold:
            issues.append(
                f"Low confidence: {confidence:.2f} < threshold {self.confidence_threshold}"
            )

        # 4. Check priority consistency
        category = ticket.get("category", "")
        priority = ticket.get("priority", "")
        expected = EXPECTED_PRIORITIES.get(category, set())
        if expected and priority not in expected:
            issues.append(
                f"Priority '{priority}' unexpected for category '{category}' "
                f"(expected: {expected})"
            )

        # 5. Spam should not have high priority
        if category == "Spam" and priority in {"Critical", "High"}:
            issues.append("Spam should not have high priority")

        # 6. Praise should not have high priority
        if category == "Praise" and priority in {"Critical", "High"}:
            issues.append("Praise feedback should have Low priority")

        return issues
