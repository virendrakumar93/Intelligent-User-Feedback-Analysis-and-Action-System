"""
Unit tests for individual agents.
"""

import csv
import tempfile
from pathlib import Path

import pytest

from core.config import ClassificationConfig, PriorityConfig, get_config
from core.logger import ProcessingLogger
from agents.csv_reader_agent import CSVReaderAgent
from agents.classifier_agent import ClassifierAgent
from agents.bug_analysis_agent import BugAnalysisAgent
from agents.feature_extractor_agent import FeatureExtractorAgent
from agents.ticket_creator_agent import TicketCreatorAgent
from agents.quality_critic_agent import QualityCriticAgent


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def logger(tmp_dir):
    return ProcessingLogger(log_path=tmp_dir / "test_log.csv")


@pytest.fixture
def sample_reviews_csv(tmp_dir):
    path = tmp_dir / "reviews.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["review_id", "user_name", "rating", "review_text", "date", "app_version", "device"]
        )
        writer.writeheader()
        writer.writerow({
            "review_id": "R001", "user_name": "alice", "rating": "1",
            "review_text": "App crashes every time I open it. Broken on iPhone.",
            "date": "2024-12-15", "app_version": "3.2.1", "device": "iPhone 14",
        })
        writer.writerow({
            "review_id": "R002", "user_name": "bob", "rating": "5",
            "review_text": "Love this app! Best productivity tool ever. Five stars!",
            "date": "2024-12-14", "app_version": "3.2.1", "device": "Pixel 8",
        })
        writer.writerow({
            "review_id": "R003", "user_name": "carol", "rating": "3",
            "review_text": "Please add dark mode support. Would be nice to have.",
            "date": "2024-12-13", "app_version": "3.2.0", "device": "Samsung Galaxy",
        })
    return path


@pytest.fixture
def sample_emails_csv(tmp_dir):
    path = tmp_dir / "emails.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["email_id", "sender", "subject", "body", "date", "priority_stated"]
        )
        writer.writeheader()
        writer.writerow({
            "email_id": "E001", "sender": "test@example.com",
            "subject": "App crashes on startup",
            "body": "Since the latest update my app crashes immediately on startup. iPhone 13 iOS 17.",
            "date": "2024-12-15", "priority_stated": "High",
        })
    return path


class TestCSVReaderAgent:
    def test_reads_reviews(self, logger, sample_reviews_csv):
        agent = CSVReaderAgent(logger)
        records = agent.execute(reviews_path=sample_reviews_csv)
        assert len(records) == 3
        assert records[0]["record_id"] == "R001"
        assert records[0]["source_type"] == "app_review"
        assert "crashes" in records[0]["text"]

    def test_reads_emails(self, logger, sample_emails_csv):
        agent = CSVReaderAgent(logger)
        records = agent.execute(emails_path=sample_emails_csv)
        assert len(records) == 1
        assert records[0]["record_id"] == "E001"
        assert records[0]["source_type"] == "support_email"

    def test_handles_missing_file(self, logger, tmp_dir):
        agent = CSVReaderAgent(logger)
        records = agent.execute(reviews_path=tmp_dir / "nonexistent.csv")
        assert records == []

    def test_reads_both_sources(self, logger, sample_reviews_csv, sample_emails_csv):
        agent = CSVReaderAgent(logger)
        records = agent.execute(
            reviews_path=sample_reviews_csv,
            emails_path=sample_emails_csv,
        )
        assert len(records) == 4


class TestClassifierAgent:
    def test_classifies_bug(self, logger):
        config = ClassificationConfig()
        agent = ClassifierAgent(logger, config)
        records = [{
            "record_id": "R001",
            "text": "app crashes every time I open it broken on iPhone",
            "metadata": {"rating": "1"},
        }]
        result = agent.execute(records)
        assert result[0]["category"] == "Bug"
        assert result[0]["confidence"] > 0

    def test_classifies_praise(self, logger):
        config = ClassificationConfig()
        agent = ClassifierAgent(logger, config)
        records = [{
            "record_id": "R002",
            "text": "love this app best productivity tool ever five stars",
            "metadata": {"rating": "5"},
        }]
        result = agent.execute(records)
        assert result[0]["category"] == "Praise"

    def test_classifies_feature_request(self, logger):
        config = ClassificationConfig()
        agent = ClassifierAgent(logger, config)
        records = [{
            "record_id": "R003",
            "text": "please add dark mode support would be nice to have a feature",
            "metadata": {},
        }]
        result = agent.execute(records)
        assert result[0]["category"] == "Feature Request"

    def test_classifies_spam(self, logger):
        config = ClassificationConfig()
        agent = ClassifierAgent(logger, config)
        records = [{
            "record_id": "S001",
            "text": "click here for free money buy now amazing deal",
            "metadata": {},
        }]
        result = agent.execute(records)
        assert result[0]["category"] == "Spam"


class TestBugAnalysisAgent:
    def test_extracts_bug_details(self, logger):
        config = PriorityConfig()
        agent = BugAnalysisAgent(logger, config)
        records = [{
            "record_id": "R001",
            "category": "Bug",
            "text": "App crashes on my iPhone 14 with iOS 17.2 using version 3.2.1",
            "metadata": {"device": "iPhone 14", "app_version": "3.2.1"},
        }]
        result = agent.execute(records)
        bug = result[0]
        assert "bug_details" in bug
        assert bug["bug_details"]["severity"] == "Critical"
        assert bug["priority"] == "Critical"

    def test_skips_non_bugs(self, logger):
        config = PriorityConfig()
        agent = BugAnalysisAgent(logger, config)
        records = [{"record_id": "R002", "category": "Praise", "text": "Great app!", "metadata": {}}]
        result = agent.execute(records)
        assert "bug_details" not in result[0]


class TestFeatureExtractorAgent:
    def test_extracts_feature_details(self, logger):
        config = PriorityConfig()
        agent = FeatureExtractorAgent(logger, config)
        records = [{
            "record_id": "R003",
            "category": "Feature Request",
            "text": "Please add dark mode support. I use the app at night.",
            "metadata": {},
        }]
        result = agent.execute(records)
        feat = result[0]
        assert "feature_details" in feat
        assert feat["feature_details"]["theme"] == "dark mode"


class TestTicketCreatorAgent:
    def test_creates_ticket(self, logger):
        agent = TicketCreatorAgent(logger)
        records = [{
            "record_id": "R001",
            "source_type": "app_review",
            "category": "Bug",
            "priority": "Critical",
            "confidence": 0.85,
            "text": "App crashes on startup",
            "bug_details": {
                "device": "iPhone 14",
                "os": "iOS 17.2",
                "app_version": "3.2.1",
                "severity": "Critical",
                "reproduction_steps": "Open app",
            },
        }]
        tickets = agent.execute(records)
        assert len(tickets) == 1
        t = tickets[0]
        assert t["ticket_id"].startswith("BUG-")
        assert t["category"] == "Bug"
        assert t["priority"] == "Critical"
        assert t["source_id"] == "R001"


class TestQualityCriticAgent:
    def test_passes_good_ticket(self, logger):
        agent = QualityCriticAgent(logger, confidence_threshold=0.5)
        tickets = [{
            "ticket_id": "BUG-0001",
            "title": "Critical crash on startup for iPhone users",
            "description": "The app crashes on startup.",
            "category": "Bug",
            "priority": "Critical",
            "source_id": "R001",
            "source_type": "app_review",
            "confidence": 0.85,
        }]
        result = agent.execute(tickets)
        assert result[0]["quality_passed"] is True

    def test_flags_low_confidence(self, logger):
        agent = QualityCriticAgent(logger, confidence_threshold=0.8)
        tickets = [{
            "ticket_id": "BUG-0001",
            "title": "Possible bug report",
            "description": "Something might be wrong.",
            "category": "Bug",
            "priority": "Medium",
            "source_id": "R001",
            "source_type": "app_review",
            "confidence": 0.3,
        }]
        result = agent.execute(tickets)
        assert result[0]["quality_passed"] is False
        assert any("Low confidence" in i for i in result[0]["quality_issues"])

    def test_flags_spam_with_high_priority(self, logger):
        agent = QualityCriticAgent(logger, confidence_threshold=0.5)
        tickets = [{
            "ticket_id": "SPM-0001",
            "title": "Spam: Flagged content",
            "description": "Buy now click here",
            "category": "Spam",
            "priority": "High",
            "source_id": "S001",
            "source_type": "app_review",
            "confidence": 0.9,
        }]
        result = agent.execute(tickets)
        assert result[0]["quality_passed"] is False
