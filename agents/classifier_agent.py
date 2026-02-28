"""
Feedback Classifier Agent — classifies feedback into categories.

Hybrid approach:
1. Rule-based keyword matching (always available)
2. Confidence score output with reasoning

Categories: Bug, Feature Request, Praise, Complaint, Spam
"""

import re
from typing import Any, Dict, List, Tuple

from agents.base_agent import BaseAgent
from core.config import ClassificationConfig
from core.logger import ProcessingLogger


class ClassifierAgent(BaseAgent):
    """Agent that classifies feedback text into predefined categories."""

    def __init__(self, logger: ProcessingLogger, config: ClassificationConfig):
        super().__init__("ClassifierAgent", logger)
        self.config = config
        self.keyword_weights = config.keyword_weights
        self.confidence_threshold = config.confidence_threshold

    def execute(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify each record and attach category, confidence, and reasoning."""
        self.log("classify", "INFO", f"Classifying {len(records)} records")
        classified = []
        for record in records:
            try:
                result = self._classify_single(record)
                classified.append(result)
            except Exception as exc:
                self.log_error(
                    "classify", str(exc), record_id=record.get("record_id", "")
                )
                record["category"] = "Unknown"
                record["confidence"] = 0.0
                record["reasoning"] = f"Classification error: {exc}"
                classified.append(record)

        self._log_distribution(classified)
        return classified

    def _classify_single(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Run hybrid classification on a single record."""
        text = record.get("text", "").lower()
        scores: Dict[str, float] = {}
        matched_keywords: Dict[str, List[str]] = {}

        for category, keywords in self.keyword_weights.items():
            category_score = 0.0
            matches: List[str] = []
            for keyword, weight in keywords.items():
                if keyword.lower() in text:
                    category_score += weight
                    matches.append(keyword)
            scores[category] = category_score
            matched_keywords[category] = matches

        # Rating boost for app reviews
        rating = record.get("metadata", {}).get("rating", "")
        if rating:
            try:
                r = int(rating)
                if r >= 4:
                    scores["Praise"] = scores.get("Praise", 0) + 0.5
                elif r <= 2:
                    scores["Bug"] = scores.get("Bug", 0) + 0.2
                    scores["Complaint"] = scores.get("Complaint", 0) + 0.3
            except ValueError:
                pass

        # Determine winning category
        if not any(scores.values()):
            category = "Complaint"
            confidence = 0.3
            reasoning = "No strong keyword matches; defaulting to Complaint"
        else:
            total = sum(scores.values()) or 1.0
            category = max(scores, key=scores.get)  # type: ignore[arg-type]
            raw_confidence = scores[category] / total
            # Scale confidence to a reasonable range
            confidence = min(round(raw_confidence, 3), 1.0)
            top_matches = matched_keywords.get(category, [])[:5]
            reasoning = (
                f"Matched keywords: {top_matches}; "
                f"score={scores[category]:.2f}/{total:.2f}"
            )

        record["category"] = category
        record["confidence"] = confidence
        record["reasoning"] = reasoning

        status = "SUCCESS" if confidence >= self.confidence_threshold else "WARNING"
        self.log(
            "classify", status,
            f"Classified as {category} (conf={confidence:.2f})",
            record_id=record.get("record_id", ""),
        )
        return record

    def _log_distribution(self, records: List[Dict[str, Any]]) -> None:
        """Log the category distribution summary."""
        dist: Dict[str, int] = {}
        for r in records:
            cat = r.get("category", "Unknown")
            dist[cat] = dist.get(cat, 0) + 1
        self.log_success(
            "summary",
            f"Classification distribution: {dist}",
        )
