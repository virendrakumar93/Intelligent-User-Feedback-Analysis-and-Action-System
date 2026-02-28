#!/usr/bin/env python3
"""
Script to generate mock CSV data for demonstration purposes.

This script recreates the sample datasets in data/ if they are missing or
need to be refreshed. It can also generate larger datasets for stress testing.

Usage:
    python scripts/generate_mock_data.py              # Generate default datasets
    python scripts/generate_mock_data.py --count 100  # Generate 100 records each
"""

import argparse
import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Sample data pools
NAMES = [
    "john_doe", "sarah_m", "tech_guru42", "angry_user99", "maria_garcia",
    "dev_fan", "frustrated_user", "product_thinker", "casual_user",
    "happy_camper", "data_worried", "ux_designer", "enterprise_user",
    "night_owl", "power_user", "new_user_2024", "feature_lover",
    "old_timer", "bug_reporter", "minimalist",
]

DEVICES = [
    "iPhone 14", "iPhone 15", "Samsung Galaxy S23", "Pixel 8",
    "iPad Pro", "Samsung Galaxy S24", "MacBook Pro", "Android",
]

BUG_TEXTS = [
    "App crashes every time I try to open my profile page. Using {device} with v{version}.",
    "Login keeps failing with error code 403. Can't access my account since update.",
    "App freezes randomly during video calls. Have to force close and restart.",
    "Black screen bug on startup since updating to v{version}. Very frustrating.",
    "All my saved projects disappeared after the update. Data loss is unacceptable.",
    "Critical crash when uploading files larger than 10MB on {device}.",
    "Sync between devices is completely broken. Changes don't appear across devices.",
]

FEATURE_TEXTS = [
    "Please add dark mode support. I use the app at night.",
    "Would love to see integration with Google Calendar and Slack.",
    "Need offline mode to access data without internet connection.",
    "Please add end-to-end encryption for shared documents.",
    "Request for educational pricing for our university.",
    "Would be nice to have a public API for integration.",
    "Please add time tracking or Pomodoro timer feature.",
]

PRAISE_TEXTS = [
    "Absolutely love this app! Best productivity app I've ever used. Five stars!",
    "Great job on the latest update! Highly recommend to everyone!",
    "This app has genuinely improved my workflow. Wonderful experience!",
    "Perfect. Simple. Clean. Does exactly what I need. Recommend to everyone!",
    "Impressed by the performance improvements. The developers clearly care.",
]

COMPLAINT_TEXTS = [
    "This is terrible! Paid for premium and sync hasn't worked for weeks. Want a refund!",
    "Horrible experience. The onboarding tutorial is confusing and misleading.",
    "Worst app update ever. You completely ruined the navigation.",
    "Disappointed with premium features. They don't justify the price at all.",
    "Furious about the pricing change. Increased by 50% with no new features.",
]

SPAM_TEXTS = [
    "Click here for FREE money!!! Visit www.totally-legit-site.com for deals!",
    "CONGRATULATIONS! You've won a $1000 gift card! Claim your prize now!",
    "Make $10000 from home! No experience needed! Visit earn-quick-cash.biz",
]


def generate_reviews(count: int) -> None:
    """Generate app_store_reviews.csv."""
    path = DATA_DIR / "app_store_reviews.csv"
    all_texts = (
        [(t, "Bug") for t in BUG_TEXTS]
        + [(t, "Feature Request") for t in FEATURE_TEXTS]
        + [(t, "Praise") for t in PRAISE_TEXTS]
        + [(t, "Complaint") for t in COMPLAINT_TEXTS]
        + [(t, "Spam") for t in SPAM_TEXTS]
    )

    rows = []
    for i in range(1, count + 1):
        text_template, _cat = random.choice(all_texts)
        device = random.choice(DEVICES)
        version = random.choice(["3.2.0", "3.2.1", "3.1.0"])
        text = text_template.format(device=device, version=version)
        date = (datetime(2024, 12, 15) - timedelta(days=i)).strftime("%Y-%m-%d")
        rating = random.randint(1, 5)

        rows.append({
            "review_id": f"R{i:03d}",
            "user_name": random.choice(NAMES),
            "rating": str(rating),
            "review_text": text,
            "date": date,
            "app_version": version,
            "device": device,
        })

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["review_id", "user_name", "rating", "review_text", "date", "app_version", "device"]
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {count} reviews -> {path}")


def generate_emails(count: int) -> None:
    """Generate support_emails.csv."""
    path = DATA_DIR / "support_emails.csv"
    all_texts = (
        [(t, "Bug") for t in BUG_TEXTS]
        + [(t, "Feature Request") for t in FEATURE_TEXTS]
        + [(t, "Praise") for t in PRAISE_TEXTS]
        + [(t, "Complaint") for t in COMPLAINT_TEXTS]
        + [(t, "Spam") for t in SPAM_TEXTS]
    )

    rows = []
    for i in range(1, count + 1):
        text_template, cat = random.choice(all_texts)
        device = random.choice(DEVICES)
        version = random.choice(["3.2.0", "3.2.1", "3.1.0"])
        text = text_template.format(device=device, version=version)
        date = (datetime(2024, 12, 15) - timedelta(days=i)).strftime("%Y-%m-%d")
        priority = random.choice(["Low", "Medium", "High", "Critical"])

        rows.append({
            "email_id": f"E{i:03d}",
            "sender": f"user{i}@example.com",
            "subject": f"Re: {cat} - ticket {i}",
            "body": text,
            "date": date,
            "priority_stated": priority,
        })

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["email_id", "sender", "subject", "body", "date", "priority_stated"]
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {count} emails -> {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate mock feedback datasets")
    parser.add_argument("--count", type=int, default=30, help="Number of records per file")
    args = parser.parse_args()

    generate_reviews(args.count)
    generate_emails(args.count)
    print("Done! Mock data generated in data/")


if __name__ == "__main__":
    main()
