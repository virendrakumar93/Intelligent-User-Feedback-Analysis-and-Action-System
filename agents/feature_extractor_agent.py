"""
Feature Extractor Agent — extracts and prioritizes feature requests.

For records classified as Feature Request, this agent:
- Extracts the feature description
- Estimates demand based on frequency-based scoring
- Assigns priority (High / Medium / Low)
"""

import re
from collections import Counter
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from core.config import PriorityConfig
from core.logger import ProcessingLogger


# Common feature themes for frequency grouping
FEATURE_THEMES = {
    "dark mode": ["dark mode", "night mode", "dark theme"],
    "offline mode": ["offline", "without internet", "no connection"],
    "integration": ["integration", "integrate", "api", "connect with"],
    "export": ["export", "download", "csv", "json", "pdf export"],
    "accessibility": ["accessibility", "screen reader", "contrast", "wcag"],
    "admin controls": ["admin", "role", "permission", "sso", "rbac"],
    "time tracking": ["time tracking", "timer", "pomodoro", "time spent"],
    "customization": ["customize", "custom", "widget", "layout", "theme"],
    "encryption": ["encryption", "encrypt", "end-to-end", "e2ee", "security"],
    "collaboration": ["collaboration", "team", "shared", "real-time"],
    "pricing": ["discount", "pricing", "educational", "bulk", "license"],
    "notifications": ["notification", "alert", "reminder"],
}


class FeatureExtractorAgent(BaseAgent):
    """Agent that analyzes feature request records."""

    def __init__(self, logger: ProcessingLogger, config: PriorityConfig):
        super().__init__("FeatureExtractorAgent", logger)
        self.thresholds = config.feature_priority_thresholds

    def execute(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze feature requests: extract description, estimate demand, assign priority."""
        features = [r for r in records if r.get("category") == "Feature Request"]
        self.log("extract", "INFO", f"Processing {len(features)} feature requests")

        # First pass: identify themes for frequency scoring
        theme_counts = self._count_themes(features)
        max_count = max(theme_counts.values()) if theme_counts else 1

        # Second pass: enrich each feature record
        for record in features:
            try:
                self._analyze_feature(record, theme_counts, max_count)
            except Exception as exc:
                self.log_error(
                    "extract", str(exc),
                    record_id=record.get("record_id", ""),
                )
                record["priority"] = "Medium"
                record["feature_details"] = {}

        return records

    def _analyze_feature(
        self,
        record: Dict[str, Any],
        theme_counts: Counter,
        max_count: int,
    ) -> None:
        """Extract feature details and assign priority for one record."""
        text = record.get("text", "")
        description = self._extract_description(text)
        theme = self._identify_theme(text)
        count = theme_counts.get(theme, 1) if theme else 1
        demand_score = round(count / max_count, 3) if max_count else 0.0

        priority = self._score_to_priority(demand_score)

        record["feature_details"] = {
            "description": description,
            "theme": theme or "other",
            "demand_score": demand_score,
            "occurrences": count,
        }
        record["priority"] = priority

        self.log_success(
            "extract",
            f"Theme={theme or 'other'}, demand={demand_score:.2f}, priority={priority}",
            record_id=record.get("record_id", ""),
        )

    def _score_to_priority(self, demand_score: float) -> str:
        """Convert demand score to priority level."""
        for level in ["High", "Medium", "Low"]:
            if demand_score >= self.thresholds.get(level, 0):
                return level
        return "Low"

    @staticmethod
    def _count_themes(records: List[Dict[str, Any]]) -> Counter:
        """Count how many records match each feature theme."""
        counts: Counter = Counter()
        for record in records:
            text = record.get("text", "").lower()
            for theme, keywords in FEATURE_THEMES.items():
                if any(kw in text for kw in keywords):
                    counts[theme] += 1
        return counts

    @staticmethod
    def _identify_theme(text: str) -> str:
        """Identify the primary feature theme of a text."""
        text_lower = text.lower()
        for theme, keywords in FEATURE_THEMES.items():
            if any(kw in text_lower for kw in keywords):
                return theme
        return ""

    @staticmethod
    def _extract_description(text: str) -> str:
        """Extract a concise feature description from the text."""
        # Try to find explicit request phrases
        patterns = [
            r"(?:please |would love to |wish |need |want )(.+?)(?:\.|$)",
            r"(?:add|include|support|implement)\s+(.+?)(?:\.|$)",
            r"(?:it would be (?:nice|great|helpful) (?:to|if) )(.+?)(?:\.|$)",
            r"(?:suggestion:\s*)(.+?)(?:\.|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                desc = match.group(1).strip()
                if len(desc) > 15:
                    return desc[:200]

        # Fallback: return first meaningful sentence
        sentences = re.split(r"[.!?]+", text)
        for s in sentences:
            s = s.strip()
            if len(s) > 20:
                return s[:200]
        return text[:200]
