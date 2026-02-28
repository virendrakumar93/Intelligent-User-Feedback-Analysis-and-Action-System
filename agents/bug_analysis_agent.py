"""
Bug Analysis Agent — extracts technical details from bug reports.

For records classified as Bug, this agent extracts:
- Device information
- OS version
- App version
- Reproduction steps (heuristic extraction)
- Severity level (Critical / High / Medium)
"""

import re
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from core.config import PriorityConfig
from core.logger import ProcessingLogger
from core.utils import extract_device_info, extract_os_info, extract_version


class BugAnalysisAgent(BaseAgent):
    """Agent that enriches bug reports with technical metadata and severity."""

    def __init__(self, logger: ProcessingLogger, config: PriorityConfig):
        super().__init__("BugAnalysisAgent", logger)
        self.severity_keywords = config.bug_severity_keywords

    def execute(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze bug records and attach technical metadata + severity."""
        bugs = [r for r in records if r.get("category") == "Bug"]
        self.log("analyze", "INFO", f"Analyzing {len(bugs)} bug reports")

        for record in bugs:
            try:
                self._analyze_bug(record)
            except Exception as exc:
                self.log_error(
                    "analyze", str(exc),
                    record_id=record.get("record_id", ""),
                )
                record.setdefault("bug_details", {})
                record["priority"] = "Medium"

        return records

    def _analyze_bug(self, record: Dict[str, Any]) -> None:
        """Extract device, OS, version, steps, and severity for one bug."""
        text = record.get("text", "")
        metadata = record.get("metadata", {})

        device = (
            extract_device_info(text)
            or metadata.get("device", "")
            or "Unknown"
        )
        os_info = extract_os_info(text) or "Unknown"
        app_version = (
            extract_version(text)
            or metadata.get("app_version", "")
            or "Unknown"
        )
        steps = self._extract_repro_steps(text)
        severity = self._determine_severity(text)

        record["bug_details"] = {
            "device": device,
            "os": os_info,
            "app_version": app_version,
            "reproduction_steps": steps,
            "severity": severity,
        }
        record["priority"] = severity

        self.log_success(
            "analyze",
            f"Severity={severity}, device={device}, os={os_info}",
            record_id=record.get("record_id", ""),
        )

    def _determine_severity(self, text: str) -> str:
        """Map bug text to severity level based on keyword matching."""
        text_lower = text.lower()
        for severity in ["Critical", "High", "Medium"]:
            keywords = self.severity_keywords.get(severity, [])
            for kw in keywords:
                if kw.lower() in text_lower:
                    return severity
        return "Medium"

    @staticmethod
    def _extract_repro_steps(text: str) -> str:
        """Heuristic extraction of reproduction steps from bug text."""
        # Look for numbered steps
        numbered = re.findall(r"\d+[.)]\s*(.+?)(?=\d+[.)]|$)", text)
        if numbered:
            return "; ".join(s.strip() for s in numbered)

        # Look for action verbs that suggest reproduction
        action_patterns = [
            r"(when I .+?)(?:\.|$)",
            r"(I tried .+?)(?:\.|$)",
            r"(after .+?)(?:\.|$)",
            r"(every time .+?)(?:\.|$)",
        ]
        steps = []
        for pattern in action_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            steps.extend(m.strip() for m in matches)

        return "; ".join(steps[:3]) if steps else "No clear reproduction steps identified"
