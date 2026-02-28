# Intelligent User Feedback Analysis and Action System

A production-grade, multi-agent AI system that automatically ingests user feedback from multiple sources, classifies it, extracts actionable insights, generates structured tickets, and provides a real-time analytics dashboard.

## Project Overview

This system processes app store reviews and support emails through a pipeline of six specialized agents, each with a clear responsibility. The pipeline classifies feedback into categories (Bug, Feature Request, Praise, Complaint, Spam), extracts technical details, assigns priority levels, generates tickets, and validates output quality — all tracked with structured logging and evaluated against ground-truth labels.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                          │
│              (core/orchestrator.py)                      │
└─────┬───────┬───────┬───────┬───────┬───────┬───────────┘
      │       │       │       │       │       │
      ▼       │       │       │       │       │
┌──────────┐  │       │       │       │       │
│ CSV      │  │       │       │       │       │
│ Reader   │──┘       │       │       │       │
│ Agent    │          │       │       │       │
└──────────┘          │       │       │       │
      │               ▼       │       │       │
      │         ┌──────────┐  │       │       │
      └────────►│Classifier│──┘       │       │
                │  Agent   │          │       │
                └──────────┘          │       │
                      │               │       │
              ┌───────┴───────┐       │       │
              ▼               ▼       │       │
        ┌──────────┐   ┌──────────┐   │       │
        │ Bug      │   │ Feature  │───┘       │
        │ Analysis │   │ Extractor│           │
        │ Agent    │   │ Agent    │           │
        └──────────┘   └──────────┘           │
              │               │               │
              └───────┬───────┘               │
                      ▼                       │
                ┌──────────┐                  │
                │ Ticket   │──────────────────┘
                │ Creator  │
                │ Agent    │
                └──────────┘
                      │
                      ▼
                ┌──────────┐
                │ Quality  │
                │ Critic   │
                │ Agent    │
                └──────────┘
                      │
                      ▼
              ┌──────────────┐
              │   OUTPUTS    │
              │ tickets.csv  │
              │ metrics.csv  │
              │  log.csv     │
              └──────────────┘
```

## Agent Responsibilities

| Agent | File | Responsibility |
|-------|------|----------------|
| **CSV Reader** | `agents/csv_reader_agent.py` | Reads input CSVs, validates schema, handles missing values, standardizes timestamps |
| **Classifier** | `agents/classifier_agent.py` | Hybrid NLP classification using keyword matching + rating boost. Outputs category, confidence, reasoning |
| **Bug Analyzer** | `agents/bug_analysis_agent.py` | Extracts device, OS, app version, reproduction steps, and severity level for bug reports |
| **Feature Extractor** | `agents/feature_extractor_agent.py` | Identifies feature themes, estimates demand via frequency scoring, assigns priority |
| **Ticket Creator** | `agents/ticket_creator_agent.py` | Generates structured tickets with ID, title, description, metadata for all records |
| **Quality Critic** | `agents/quality_critic_agent.py` | Validates tickets: title clarity, priority consistency, confidence thresholds, flags issues |

## Repository Structure

```
├── agents/                          # Multi-agent modules
│   ├── base_agent.py                # Abstract base class for all agents
│   ├── csv_reader_agent.py          # Data ingestion & validation
│   ├── classifier_agent.py          # NLP feedback classification
│   ├── bug_analysis_agent.py        # Bug report analysis
│   ├── feature_extractor_agent.py   # Feature request extraction
│   ├── ticket_creator_agent.py      # Ticket generation
│   └── quality_critic_agent.py      # Quality validation
├── core/                            # Core system modules
│   ├── config.py                    # Centralized configuration
│   ├── logger.py                    # Structured CSV + console logging
│   ├── metrics.py                   # Evaluation metrics computation
│   ├── orchestrator.py              # Pipeline orchestration
│   └── utils.py                     # Utility functions
├── data/                            # Input datasets
│   ├── app_store_reviews.csv        # 30 sample app store reviews
│   ├── support_emails.csv           # 20 sample support emails
│   └── expected_classifications.csv # Ground-truth labels for evaluation
├── outputs/                         # Generated output files (runtime)
│   ├── generated_tickets.csv        # Structured tickets
│   ├── processing_log.csv           # Processing history
│   └── metrics.csv                  # Evaluation metrics
├── scripts/
│   └── generate_mock_data.py        # Script to generate larger test datasets
├── tests/                           # Test suite
│   ├── test_agents.py               # Unit tests for each agent
│   └── test_pipeline.py             # Integration tests for full pipeline
├── ui/
│   └── streamlit_app.py             # Streamlit dashboard
├── main.py                          # CLI entry point
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variable template
└── .gitignore
```

## Setup Instructions

```bash
# Clone the repository
git clone https://github.com/virendrakumar93/Intelligent-User-Feedback-Analysis-and-Action-System.git
cd Intelligent-User-Feedback-Analysis-and-Action-System

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## How to Run

### Run the Pipeline (CLI)

```bash
python main.py
```

With verbose logging:

```bash
python main.py --verbose
```

### Launch the Dashboard

```bash
streamlit run ui/streamlit_app.py
```

The dashboard will open at `http://localhost:8501` and includes:
- **Processing Overview** — Total records, category/priority distribution charts
- **Ticket Viewer** — Editable table with filtering and manual override
- **Analytics** — Accuracy, precision/recall/F1 per category, low-confidence flags
- **Processing Logs** — Full log viewer with status filtering and CSV download

### Run Tests

```bash
python -m pytest tests/ -v
```

### Generate Custom Mock Data

```bash
python scripts/generate_mock_data.py --count 100
```

## How to Modify Configuration

All system parameters are centralized in `core/config.py`:

```python
from core.config import get_config

config = get_config()

# Adjust classification confidence threshold
config.classification.confidence_threshold = 0.7

# Modify bug severity keywords
config.priority.bug_severity_keywords["Critical"].append("memory leak")

# Change feature priority thresholds
config.priority.feature_priority_thresholds["High"] = 0.8
```

Key configurable parameters:
- `confidence_threshold` — Minimum confidence to accept classification (default: 0.6)
- `keyword_weights` — Per-category keyword-to-weight mapping for classification
- `bug_severity_keywords` — Keywords that map to Critical/High/Medium severity
- `feature_priority_thresholds` — Demand score thresholds for feature priority
- `log_level` — Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- File paths — All input/output file locations

## Example Output

### Pipeline Summary
```
Total tickets generated : 50
Processing time         : 0.07s
Overall accuracy        : 90.00%
Average confidence      : 76.04%

Tickets per category:
    Bug                 : 14
    Feature Request     : 14
    Praise              : 13
    Complaint           : 5
    Spam                : 4
```

### Sample Generated Ticket
```
ticket_id  : BUG-0001
title      : [Critical] App crashes every time I try to open my profile page
category   : Bug
priority   : Critical
confidence : 0.87
device     : iPhone 14
os         : iOS 17.2
app_version: 3.2.1
severity   : Critical
```

## Evaluation Results

Against the provided ground-truth labels (`expected_classifications.csv`):

| Category        | Precision | Recall | F1 Score |
|-----------------|-----------|--------|----------|
| Bug             | 1.000     | 1.000  | 1.000    |
| Complaint       | 1.000     | 0.833  | 0.909    |
| Feature Request | 0.857     | 0.800  | 0.828    |
| Praise          | 0.769     | 1.000  | 0.870    |
| Spam            | 1.000     | 0.800  | 0.889    |
| **Overall**     |           |        | **90.0% accuracy** |

## Future Improvements

- **LLM Classification Layer** — Add OpenAI/Anthropic API integration for high-confidence classification when rule-based confidence is low
- **CrewAI/AutoGen Integration** — Migrate agents to CrewAI framework for advanced inter-agent communication
- **Semantic Similarity** — Use sentence embeddings for theme clustering and duplicate detection
- **Real-time Ingestion** — Add webhook/API endpoints for live feedback processing
- **Database Backend** — Replace CSV storage with PostgreSQL for production workloads
- **Authentication** — Add user authentication to the Streamlit dashboard
- **Export Formats** — Support JIRA, GitHub Issues, and Linear ticket export
- **Multi-language Support** — Add translation layer for non-English feedback

## Assumptions & Limitations

- **Rule-based Classification**: The current classifier uses keyword matching, which works well for clear-cut cases but may struggle with nuanced or ambiguous feedback. The system is designed to be extended with an LLM layer.
- **English Only**: The system processes English-language feedback only.
- **CSV-based**: Input/output uses CSV files. For production, a database backend is recommended.
- **No External API Dependencies**: The system runs entirely locally with no external API calls, ensuring privacy and offline capability.
- **Confidence Scores**: Confidence values are derived from keyword coverage ratios, not probabilistic model outputs. They indicate classification certainty within the rule-based framework.
- **Sample Data**: The included datasets (30 reviews + 20 emails) are synthetic but representative of real-world feedback patterns.

## Technology Stack

- **Python 3.11+**
- **Streamlit** — Interactive dashboard
- **Pandas** — Data manipulation
- **Pytest** — Testing framework

## License

MIT License
