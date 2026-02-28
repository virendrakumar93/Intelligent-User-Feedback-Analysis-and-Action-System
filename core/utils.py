"""
Utility functions for the Intelligent Feedback Analysis System.
"""

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def sanitize_text(text: str) -> str:
    """Clean and normalize feedback text."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]+>", "", text)  # strip HTML tags
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_timestamp(value: str) -> Optional[str]:
    """Attempt to parse various timestamp formats into ISO format."""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%B %d, %Y",
    ]
    if not isinstance(value, str) or not value.strip():
        return None
    for fmt in formats:
        try:
            dt = datetime.strptime(value.strip(), fmt)
            return dt.isoformat()
        except ValueError:
            continue
    return value.strip()


def generate_ticket_id(index: int, category: str) -> str:
    """Generate a unique ticket ID from index and category."""
    prefix_map = {
        "Bug": "BUG",
        "Feature Request": "FEAT",
        "Praise": "PRS",
        "Complaint": "CMP",
        "Spam": "SPM",
    }
    prefix = prefix_map.get(category, "TKT")
    return f"{prefix}-{index:04d}"


def read_csv_safe(path: Path) -> List[Dict[str, Any]]:
    """Read a CSV file and return list of row dicts with error handling."""
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    """Write a list of dicts to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def extract_version(text: str) -> Optional[str]:
    """Extract app version string from text (e.g., 'v2.3.1', 'version 4.0')."""
    patterns = [
        r"v(\d+\.\d+(?:\.\d+)?)",
        r"version\s*(\d+\.\d+(?:\.\d+)?)",
        r"(\d+\.\d+\.\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_device_info(text: str) -> Optional[str]:
    """Extract device/platform information from text."""
    devices = [
        "iPhone", "iPad", "Samsung", "Pixel", "Galaxy", "Android",
        "iOS", "Huawei", "OnePlus", "Xiaomi", "MacBook", "Windows",
        "Linux", "Chrome OS", "tablet", "phone",
    ]
    text_lower = text.lower()
    found = [d for d in devices if d.lower() in text_lower]
    return ", ".join(found) if found else None


def extract_os_info(text: str) -> Optional[str]:
    """Extract operating system information from text."""
    os_patterns = [
        r"(iOS\s*\d+(?:\.\d+)?)",
        r"(Android\s*\d+(?:\.\d+)?)",
        r"(Windows\s*\d+)",
        r"(macOS\s*\w+(?:\s*\d+(?:\.\d+)?)?)",
    ]
    for pattern in os_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None
