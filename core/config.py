"""
Configuration module for the Intelligent Feedback Analysis System.

Provides centralized, config-driven architecture with all tunable parameters.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory paths
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DOCS_DIR = PROJECT_ROOT / "docs"


@dataclass
class ClassificationConfig:
    """Configuration for the feedback classification system."""

    confidence_threshold: float = 0.6
    categories: List[str] = field(default_factory=lambda: [
        "Bug", "Feature Request", "Praise", "Complaint", "Spam"
    ])
    # Keyword weights for rule-based classification
    keyword_weights: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "Bug": {
            "crash": 0.9, "bug": 0.9, "error": 0.85, "broken": 0.85,
            "not working": 0.8, "fail": 0.8, "freeze": 0.75, "stuck": 0.7,
            "glitch": 0.8, "issue": 0.5, "problem": 0.6, "fix": 0.5,
            "won't load": 0.8, "can't open": 0.75, "slow": 0.4,
            "unresponsive": 0.7, "black screen": 0.8, "force close": 0.85,
            "data loss": 0.9, "lost my": 0.7, "disappeared": 0.7,
            "login fail": 0.8, "sync": 0.5, "update broke": 0.85,
        },
        "Feature Request": {
            "add": 0.6, "feature": 0.8, "wish": 0.7, "would be nice": 0.8,
            "suggestion": 0.8, "please include": 0.8, "should have": 0.7,
            "need": 0.5, "want": 0.5, "improve": 0.5, "could you": 0.6,
            "it would help": 0.75, "missing": 0.4, "request": 0.7,
            "dark mode": 0.85, "integration": 0.6, "support for": 0.7,
            "option to": 0.7, "ability to": 0.7, "allow": 0.5,
        },
        "Praise": {
            "love": 0.8, "great": 0.7, "awesome": 0.8, "excellent": 0.85,
            "amazing": 0.85, "best": 0.7, "perfect": 0.8, "fantastic": 0.85,
            "wonderful": 0.8, "thank": 0.6, "good job": 0.8,
            "well done": 0.8, "helpful": 0.6, "recommend": 0.7,
            "five stars": 0.9, "5 stars": 0.9, "intuitive": 0.7,
            "beautiful": 0.7, "smooth": 0.6, "impressed": 0.8,
        },
        "Complaint": {
            "terrible": 0.85, "worst": 0.85, "hate": 0.8, "awful": 0.85,
            "horrible": 0.85, "disappointed": 0.8, "frustrating": 0.8,
            "annoying": 0.7, "waste": 0.7, "useless": 0.8,
            "poor": 0.6, "bad": 0.6, "unacceptable": 0.85,
            "ridiculous": 0.7, "overpriced": 0.7, "scam": 0.8,
            "regret": 0.75, "misleading": 0.7, "uninstall": 0.7,
            "refund": 0.8, "angry": 0.75, "furious": 0.85,
        },
        "Spam": {
            "click here": 0.9, "free money": 0.95, "buy now": 0.9,
            "limited offer": 0.85, "act now": 0.85, "winner": 0.8,
            "congratulations": 0.7, "earn money": 0.9, "discount code": 0.8,
            "subscribe": 0.5, "visit my": 0.85, "check out my": 0.8,
            "http://": 0.6, "www.": 0.5, "promo": 0.7,
            "casino": 0.9, "lottery": 0.9, "viagra": 0.95,
        },
    })


@dataclass
class PriorityConfig:
    """Configuration for priority assignment."""

    priority_levels: List[str] = field(default_factory=lambda: [
        "Critical", "High", "Medium", "Low"
    ])
    # Bug severity mapping
    bug_severity_keywords: Dict[str, List[str]] = field(default_factory=lambda: {
        "Critical": [
            "crash", "data loss", "lost my", "disappeared", "corrupt",
            "black screen", "force close", "bricked", "won't start",
        ],
        "High": [
            "login", "can't access", "sync", "payment", "security",
            "authentication", "password", "account locked", "not loading",
        ],
        "Medium": [
            "slow", "lag", "delay", "minor", "cosmetic", "alignment",
            "typo", "formatting", "color", "font",
        ],
    })
    # Feature request priority thresholds (based on frequency score)
    feature_priority_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "High": 0.7,
        "Medium": 0.4,
        "Low": 0.0,
    })


@dataclass
class PipelineConfig:
    """Main pipeline configuration."""

    # File paths
    app_reviews_path: Path = DATA_DIR / "app_store_reviews.csv"
    support_emails_path: Path = DATA_DIR / "support_emails.csv"
    expected_classifications_path: Path = DATA_DIR / "expected_classifications.csv"
    tickets_output_path: Path = OUTPUTS_DIR / "generated_tickets.csv"
    processing_log_path: Path = OUTPUTS_DIR / "processing_log.csv"
    metrics_output_path: Path = OUTPUTS_DIR / "metrics.csv"

    # Classification settings
    classification: ClassificationConfig = field(
        default_factory=ClassificationConfig
    )

    # Priority settings
    priority: PriorityConfig = field(default_factory=PriorityConfig)

    # Logging
    log_level: str = "INFO"

    # Processing
    batch_size: int = 50
    max_retries: int = 3


def get_config() -> PipelineConfig:
    """Return the default pipeline configuration."""
    return PipelineConfig()
