"""
Streamlit Dashboard for the Intelligent User Feedback Analysis System.

Features:
1. Processing Overview — totals, category distribution, priority distribution
2. Ticket Table Viewer — editable table with manual override
3. Configuration Panel — confidence threshold, priority mapping, re-run button
4. Analytics — accuracy metrics, processing log viewer, low-confidence flags
"""

import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import pandas as pd
import streamlit as st

from core.config import PipelineConfig, get_config, OUTPUTS_DIR, DATA_DIR
from core.orchestrator import PipelineOrchestrator


# ──────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Feedback Analysis Dashboard",
    page_icon="📊",
    layout="wide",
)


def load_tickets() -> pd.DataFrame:
    """Load generated tickets CSV."""
    path = OUTPUTS_DIR / "generated_tickets.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def load_metrics() -> pd.DataFrame:
    """Load metrics CSV."""
    path = OUTPUTS_DIR / "metrics.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def load_processing_log() -> pd.DataFrame:
    """Load processing log CSV."""
    path = OUTPUTS_DIR / "processing_log.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def get_metric_value(metrics_df: pd.DataFrame, metric_name: str) -> str:
    """Extract a single metric value from the metrics dataframe."""
    if metrics_df.empty:
        return "N/A"
    row = metrics_df[metrics_df["metric"] == metric_name]
    if row.empty:
        return "N/A"
    return row.iloc[0]["value"]


# ──────────────────────────────────────────────
# Sidebar — Configuration Panel
# ──────────────────────────────────────────────
st.sidebar.title("⚙️ Configuration")

confidence_threshold = st.sidebar.slider(
    "Confidence Threshold",
    min_value=0.0, max_value=1.0, value=0.6, step=0.05,
    help="Minimum confidence score to consider a classification reliable.",
)

st.sidebar.subheader("Priority Mapping")
bug_critical = st.sidebar.text_input(
    "Bug → Critical keywords",
    value="crash, data loss, force close",
)
bug_high = st.sidebar.text_input(
    "Bug → High keywords",
    value="login, sync, payment, authentication",
)
feature_high_threshold = st.sidebar.slider(
    "Feature Request → High demand threshold",
    min_value=0.0, max_value=1.0, value=0.7, step=0.05,
)

if st.sidebar.button("🔄 Re-run Pipeline", type="primary"):
    with st.spinner("Running pipeline..."):
        config = get_config()
        config.classification.confidence_threshold = confidence_threshold
        orchestrator = PipelineOrchestrator(config)
        results = orchestrator.run()
        st.sidebar.success(
            f"Pipeline complete! {len(results['tickets'])} tickets generated."
        )
        st.rerun()


# ──────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────
tickets_df = load_tickets()
metrics_df = load_metrics()
log_df = load_processing_log()

# ──────────────────────────────────────────────
# Main title
# ──────────────────────────────────────────────
st.title("📊 Intelligent Feedback Analysis Dashboard")

if tickets_df.empty:
    st.warning(
        "No pipeline output found. Click **Re-run Pipeline** in the sidebar, "
        "or run `python main.py` from the terminal first."
    )
    st.stop()


# ──────────────────────────────────────────────
# Tab layout
# ──────────────────────────────────────────────
tab_overview, tab_tickets, tab_analytics, tab_logs = st.tabs(
    ["📈 Processing Overview", "🎫 Ticket Viewer", "📊 Analytics", "📋 Logs"]
)


# ──────────────────────────────────────────────
# Tab 1 — Processing Overview
# ──────────────────────────────────────────────
with tab_overview:
    st.header("Processing Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tickets", len(tickets_df))
    col2.metric("Accuracy", get_metric_value(metrics_df, "overall_accuracy"))
    col3.metric("Avg Confidence", get_metric_value(metrics_df, "avg_confidence"))
    col4.metric(
        "Processing Time",
        f"{get_metric_value(metrics_df, 'processing_time_seconds')}s",
    )

    st.subheader("Category Distribution")
    if "category" in tickets_df.columns:
        cat_counts = tickets_df["category"].value_counts()
        st.bar_chart(cat_counts)

    st.subheader("Priority Distribution")
    if "priority" in tickets_df.columns:
        pri_counts = tickets_df["priority"].value_counts()
        col_left, col_right = st.columns(2)
        with col_left:
            st.bar_chart(pri_counts)
        with col_right:
            st.dataframe(
                pri_counts.reset_index().rename(
                    columns={"index": "Priority", "priority": "Count"}
                ),
                use_container_width=True,
            )


# ──────────────────────────────────────────────
# Tab 2 — Ticket Viewer with Manual Override
# ──────────────────────────────────────────────
with tab_tickets:
    st.header("Ticket Viewer & Manual Override")

    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        cat_filter = st.multiselect(
            "Filter by Category",
            options=sorted(tickets_df["category"].unique()) if "category" in tickets_df.columns else [],
            default=[],
        )
    with col_f2:
        pri_filter = st.multiselect(
            "Filter by Priority",
            options=sorted(tickets_df["priority"].unique()) if "priority" in tickets_df.columns else [],
            default=[],
        )

    filtered = tickets_df.copy()
    if cat_filter:
        filtered = filtered[filtered["category"].isin(cat_filter)]
    if pri_filter:
        filtered = filtered[filtered["priority"].isin(pri_filter)]

    display_cols = [
        "ticket_id", "title", "category", "priority",
        "confidence", "source_id", "source_type", "quality_passed",
    ]
    available_cols = [c for c in display_cols if c in filtered.columns]

    edited_df = st.data_editor(
        filtered[available_cols],
        use_container_width=True,
        num_rows="fixed",
        key="ticket_editor",
    )

    if st.button("💾 Save Overrides"):
        # Merge edits back into full dataframe
        for col in ["category", "priority"]:
            if col in edited_df.columns:
                for idx in edited_df.index:
                    if idx in tickets_df.index:
                        tickets_df.at[idx, col] = edited_df.at[idx, col]
        output_path = OUTPUTS_DIR / "generated_tickets.csv"
        tickets_df.to_csv(output_path, index=False)
        st.success("Overrides saved to generated_tickets.csv!")


# ──────────────────────────────────────────────
# Tab 3 — Analytics
# ──────────────────────────────────────────────
with tab_analytics:
    st.header("Classification Metrics")

    if not metrics_df.empty:
        # Overall metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Overall Accuracy", get_metric_value(metrics_df, "overall_accuracy"))
        col2.metric("Correct Predictions", get_metric_value(metrics_df, "correct_predictions"))
        col3.metric("Total Expected", get_metric_value(metrics_df, "total_expected"))

        # Per-category table
        st.subheader("Per-Category Precision / Recall / F1")
        per_cat_rows = []
        categories = ["Bug", "Feature Request", "Praise", "Complaint", "Spam"]
        for cat in categories:
            p = get_metric_value(metrics_df, f"{cat}_precision")
            r = get_metric_value(metrics_df, f"{cat}_recall")
            f1 = get_metric_value(metrics_df, f"{cat}_f1")
            if p != "N/A":
                per_cat_rows.append({
                    "Category": cat,
                    "Precision": p,
                    "Recall": r,
                    "F1 Score": f1,
                })
        if per_cat_rows:
            st.dataframe(pd.DataFrame(per_cat_rows), use_container_width=True)

    # Low-confidence flags
    st.subheader("Low-Confidence Tickets")
    if "confidence" in tickets_df.columns:
        low_conf = tickets_df[
            tickets_df["confidence"].astype(float) < confidence_threshold
        ]
        if not low_conf.empty:
            display = [c for c in ["ticket_id", "title", "category", "confidence", "quality_issues"]
                       if c in low_conf.columns]
            st.dataframe(low_conf[display], use_container_width=True)
        else:
            st.info("No low-confidence tickets found.")


# ──────────────────────────────────────────────
# Tab 4 — Processing Logs
# ──────────────────────────────────────────────
with tab_logs:
    st.header("Processing Log")

    if not log_df.empty:
        # Status filter
        status_filter = st.multiselect(
            "Filter by Status",
            options=sorted(log_df["status"].unique()) if "status" in log_df.columns else [],
            default=[],
        )
        display_log = log_df.copy()
        if status_filter:
            display_log = display_log[display_log["status"].isin(status_filter)]

        st.dataframe(display_log, use_container_width=True, height=500)

        # Download button
        csv_data = display_log.to_csv(index=False)
        st.download_button(
            "📥 Download Log CSV",
            data=csv_data,
            file_name="processing_log.csv",
            mime="text/csv",
        )
    else:
        st.info("No processing log available. Run the pipeline first.")
