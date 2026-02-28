#!/usr/bin/env python3
"""
Intelligent User Feedback Analysis and Action System

Main entry point for the multi-agent feedback processing pipeline.

Usage:
    python main.py              # Run full pipeline
    python main.py --verbose    # Run with DEBUG logging
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config import get_config
from core.orchestrator import PipelineOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Intelligent User Feedback Analysis and Action System",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG-level logging",
    )
    args = parser.parse_args()

    config = get_config()
    if args.verbose:
        config.log_level = "DEBUG"

    # Ensure output directory exists
    config.tickets_output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  Intelligent User Feedback Analysis System")
    print("  Multi-Agent Pipeline")
    print("=" * 60)
    print()

    orchestrator = PipelineOrchestrator(config)
    results = orchestrator.run()

    # Print summary
    metrics = results.get("metrics", {})
    tickets = results.get("tickets", [])
    processing_time = results.get("processing_time", 0.0)

    print()
    print("=" * 60)
    print("  PIPELINE RESULTS SUMMARY")
    print("=" * 60)
    print(f"  Total tickets generated : {len(tickets)}")
    print(f"  Processing time         : {processing_time:.2f}s")
    print(f"  Overall accuracy        : {metrics.get('overall_accuracy', 0):.2%}")
    print(f"  Average confidence      : {metrics.get('avg_confidence', 0):.2%}")
    print()

    print("  Tickets per category:")
    for cat, count in sorted(metrics.get("tickets_per_category", {}).items()):
        print(f"    {cat:20s}: {count}")
    print()

    print("  Priority distribution:")
    for pri, count in sorted(metrics.get("priority_distribution", {}).items()):
        print(f"    {pri:20s}: {count}")
    print()

    print("  Per-category metrics:")
    for cat, vals in sorted(metrics.get("per_category", {}).items()):
        p = vals.get("precision", 0)
        r = vals.get("recall", 0)
        f = vals.get("f1", 0)
        print(f"    {cat:20s}: P={p:.3f}  R={r:.3f}  F1={f:.3f}")
    print()

    print(f"  Output files:")
    print(f"    Tickets  : {config.tickets_output_path}")
    print(f"    Metrics  : {config.metrics_output_path}")
    print(f"    Log      : {config.processing_log_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
