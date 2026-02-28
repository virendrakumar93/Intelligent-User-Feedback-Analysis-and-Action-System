"""
Metrics & Evaluation module.

Computes classification accuracy, precision, recall, F1 per category,
average confidence, processing time, tickets per category, and priority distribution.
Compares predictions vs expected_classifications.csv.
"""

import csv
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def compute_metrics(
    tickets: List[Dict[str, Any]],
    expected_path: Path,
    processing_time: float,
) -> Dict[str, Any]:
    """Compute all evaluation metrics and return as a structured dict.

    Returns:
        Dict with keys: overall_accuracy, per_category (precision/recall/f1),
        avg_confidence, processing_time_seconds, tickets_per_category,
        priority_distribution, total_tickets, rows (flat list for CSV export).
    """
    expected = _load_expected(expected_path)

    # Build prediction map: source_id -> (predicted_category, predicted_priority)
    pred_map: Dict[str, Tuple[str, str]] = {}
    for t in tickets:
        sid = t.get("source_id", "")
        pred_map[sid] = (t.get("category", ""), t.get("priority", ""))

    categories = sorted({v[0] for v in pred_map.values()} | {v[0] for v in expected.values()})

    # Per-category TP/FP/FN
    tp: Dict[str, int] = {c: 0 for c in categories}
    fp: Dict[str, int] = {c: 0 for c in categories}
    fn: Dict[str, int] = {c: 0 for c in categories}
    correct = 0
    total = 0

    for record_id, (exp_cat, _exp_pri) in expected.items():
        pred_cat, _pred_pri = pred_map.get(record_id, ("", ""))
        if not pred_cat:
            fn[exp_cat] = fn.get(exp_cat, 0) + 1
            total += 1
            continue
        total += 1
        if pred_cat == exp_cat:
            correct += 1
            tp[exp_cat] = tp.get(exp_cat, 0) + 1
        else:
            fp[pred_cat] = fp.get(pred_cat, 0) + 1
            fn[exp_cat] = fn.get(exp_cat, 0) + 1

    overall_accuracy = round(correct / total, 4) if total else 0.0

    per_category: Dict[str, Dict[str, float]] = {}
    for cat in categories:
        precision = tp[cat] / (tp[cat] + fp[cat]) if (tp[cat] + fp[cat]) else 0.0
        recall = tp[cat] / (tp[cat] + fn[cat]) if (tp[cat] + fn[cat]) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        per_category[cat] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "true_positives": tp[cat],
            "false_positives": fp[cat],
            "false_negatives": fn[cat],
        }

    # Aggregate stats
    confidences = [t.get("confidence", 0) for t in tickets if isinstance(t.get("confidence"), (int, float))]
    avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0

    tickets_per_category: Dict[str, int] = {}
    priority_distribution: Dict[str, int] = {}
    for t in tickets:
        cat = t.get("category", "Unknown")
        pri = t.get("priority", "Unknown")
        tickets_per_category[cat] = tickets_per_category.get(cat, 0) + 1
        priority_distribution[pri] = priority_distribution.get(pri, 0) + 1

    return {
        "overall_accuracy": overall_accuracy,
        "per_category": per_category,
        "avg_confidence": avg_confidence,
        "processing_time_seconds": round(processing_time, 2),
        "total_tickets": len(tickets),
        "total_expected": total,
        "correct_predictions": correct,
        "tickets_per_category": tickets_per_category,
        "priority_distribution": priority_distribution,
    }


def save_metrics_csv(metrics: Dict[str, Any], output_path: Path) -> None:
    """Flatten metrics into rows and write to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, str]] = []

    rows.append({"metric": "overall_accuracy", "value": str(metrics["overall_accuracy"])})
    rows.append({"metric": "avg_confidence", "value": str(metrics["avg_confidence"])})
    rows.append({"metric": "processing_time_seconds", "value": str(metrics["processing_time_seconds"])})
    rows.append({"metric": "total_tickets", "value": str(metrics["total_tickets"])})
    rows.append({"metric": "total_expected", "value": str(metrics["total_expected"])})
    rows.append({"metric": "correct_predictions", "value": str(metrics["correct_predictions"])})

    for cat, vals in metrics.get("per_category", {}).items():
        for k, v in vals.items():
            rows.append({"metric": f"{cat}_{k}", "value": str(v)})

    for cat, count in metrics.get("tickets_per_category", {}).items():
        rows.append({"metric": f"tickets_{cat}", "value": str(count)})

    for pri, count in metrics.get("priority_distribution", {}).items():
        rows.append({"metric": f"priority_{pri}", "value": str(count)})

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(rows)


def _load_expected(path: Path) -> Dict[str, Tuple[str, str]]:
    """Load expected_classifications.csv into a dict keyed by record_id."""
    result: Dict[str, Tuple[str, str]] = {}
    if not path.exists():
        return result
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = row.get("record_id", "")
            cat = row.get("expected_category", "")
            pri = row.get("expected_priority", "")
            if rid:
                result[rid] = (cat, pri)
    return result
