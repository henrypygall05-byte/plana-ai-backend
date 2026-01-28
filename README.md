# Plana.AI Backend

AI-powered planning intelligence platform for UK planning applications. Generates structured case officer-style planning reports with policy citations, similar case analysis, and recommendations.

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install package (demo mode - no external dependencies)
pip install -e .

# Initialize the system
plana init

# List available demo applications
plana demo

# Process an application and generate a report (demo mode)
plana process 2024/0930/01/DET --mode demo --output report.md
```

### Live Mode (Portal Access)

To fetch real applications from council planning portals:

```bash
# Install with live dependencies
pip install -e '.[live]'

# Process a real Newcastle application
plana process 2026/0101/01/NPA --mode live --output report.md

# With explicit council flag
plana process 2024/0930/01/DET --mode live --council newcastle --output report.md
```

**Note**: Live mode may encounter 403 errors if the portal blocks automated access.
See [Portal Access Issues](#portal-access-issues) below.

## Features

- **Policy Retrieval**: Retrieves relevant policies from NPPF, Core Strategy (CSUCP), and Development Allocations Plan (DAP) with page citations
- **Similar Case Search**: Finds similar historic planning applications for precedent analysis
- **Report Generation**: Creates structured Markdown reports with all required sections
- **Offline-First**: Works entirely offline with demo data - no API keys or external services required
- **Live Portal Access**: Fetches real applications from council planning portals (Newcastle supported)
- **SQLite Storage**: Persists applications, documents, and reports locally

## Available Commands

```bash
plana --help                                                    # Show help
plana init                                                      # Initialize the system
plana demo                                                      # List available demo applications
plana status                                                    # Show database statistics

# Demo mode (offline, fixture data)
plana process <ref> --mode demo --output report.md

# Live mode (fetches from council portal)
plana process <ref> --mode live --output report.md
plana process <ref> --mode live --council newcastle --output report.md

# Batch evaluation
plana evaluate --refs refs.txt --mode demo --output eval_results.csv

# Quality Control (compare against real case officer decisions)
plana qc --gold eval_gold.csv --results eval_results.csv --out qc_report.md

# End-to-end benchmark
plana benchmark --mode demo --out-dir eval_run

# Feedback (for training)
plana feedback <ref> --decision APPROVE --notes "Good design"
```

## Demo Applications

| Reference | Description | Constraints |
|-----------|-------------|-------------|
| `2024/0930/01/DET` | T J Hughes extension | Conservation Area, Listed Buildings |
| `2024/0943/01/LBC` | T J Hughes listed building consent | Listed Building, Conservation Area |
| `2024/0300/01/LBC` | Grainger Street shopfront | Listed Building, Conservation Area |
| `2025/0015/01/DET` | Town Moor drainage | Town Moor, Flood Zone 2 |
| `2023/1500/01/HOU` | Jesmond Road householder | None |

## Portal Access Issues

When using `--mode live`, you may encounter a **403 Forbidden** error:

```
PORTAL ACCESS ERROR
  Error:   Access blocked by portal (403 Forbidden)
  URL:     https://publicaccess.newcastle.gov.uk/online-applications/...
  Status:  403
```

**Why this happens**: Many council planning portals use bot protection to prevent automated scraping.

**Solutions**:
1. **Wait and retry**: Sometimes waiting a few minutes resolves temporary blocks
2. **Use demo mode**: `plana process <ref> --mode demo` works offline with fixture data
3. **Browser session mode** (future): Will allow authenticated browser sessions
4. **Playwright mode** (future): Will use headless browser automation

**Supported councils**: Currently only `newcastle` is supported. More councils will be added.

## Quality Control (QC) System

The QC system measures how often Plana's decisions match real Newcastle case officer outcomes.

### QC Score Meaning

| Score | Interpretation |
|-------|----------------|
| 70-100% | **PASS**: Comparable to junior/mid case officer consistency |
| 50-70% | Moderate agreement, needs improvement |
| 0-50% | Low agreement, significant calibration needed |

### Scoring Rules

- **Exact Match (1.0 points)**: Plana and officer made the same decision
- **Partial Match (0.5 points)**: Both approved, but one with conditions and one without (APPROVE ↔ APPROVE_WITH_CONDITIONS)
- **Miss (0.0 points)**: Fundamental disagreement (APPROVE vs REFUSE) or unknown decision

### Gold File Format (eval_gold.csv)

```csv
reference,actual_decision
2025/2090/01/LDC,APPROVE
2025/1974/01/HOU,APPROVE_WITH_CONDITIONS
2025/1985/01/TCA,REFUSE
```

Valid decisions: `APPROVE`, `APPROVE_WITH_CONDITIONS`, `REFUSE`

### Running Benchmarks

```bash
# Quick benchmark with demo mode (auto-generates refs and gold template)
plana benchmark --mode demo --out-dir eval_run

# This creates:
#   eval_run/eval_refs.txt       - 10 default Newcastle references
#   eval_run/eval_gold_template.csv - Template to fill with actual decisions
#   eval_run/eval_results.csv    - Plana's decisions
#   eval_run/qc_report.md        - Full QC analysis report

# Custom benchmark with your own gold file
plana benchmark --refs my_refs.txt --gold my_gold.csv --mode demo --out-dir eval_run

# Separate QC run (after evaluate)
plana evaluate --refs refs.txt --mode demo --output results.csv
plana qc --gold gold.csv --results results.csv --out qc_report.md
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | QC score >= 70% (PASS) |
| 1 | Parse/file/runtime error |
| 2 | QC score < 70% (FAIL) |

### Default Benchmark Set

The following 10 Newcastle applications are used as the default benchmark:

```
2025/2090/01/LDC
2025/1974/01/HOU
2025/1985/01/TCA
2025/1739/01/TPO
2025/1710/01/DET
2025/1617/01/LBC
2025/0890/01/TPO
2025/0486/04/DCC
2023/0899/03/DCC
2021/1622/02/DCC
```

## Report Structure

Generated reports include:

1. **Executive Summary** - Application overview and recommendation
2. **Site and Surroundings** - Site description and context
3. **Proposal Description** - Details of the proposed development
4. **Planning History** - Relevant previous applications
5. **Policy Context** - NPPF, CSUCP, and DAP policy citations with page numbers
6. **Assessment** - Heritage impact, design, amenity analysis
7. **Similar Cases** - Historic precedents with decisions
8. **Planning Balance** - Weighing benefits against concerns
9. **Recommendation** - Decision and conditions
10. **Documents Reviewed** - List of submitted documents
11. **Evidence Appendix** - Full citation list

## Project Structure

```
plana/
├── __init__.py           # Package init
├── cli.py                # Command-line interface
├── policy/               # Policy extraction and search
│   ├── __init__.py
│   ├── extractor.py      # PDF text extraction with caching
│   ├── search.py         # TF-IDF keyword search
│   └── demo_policies.py  # Demo policy content
├── similarity/           # Similar case search
│   ├── __init__.py
│   └── search.py         # Similarity matching
├── documents/            # Document management
│   ├── __init__.py
│   └── manager.py        # Document listing and download
├── report/               # Report generation
│   ├── __init__.py
│   └── generator.py      # Markdown report generator
├── ingestion/            # Portal data fetching (live mode)
│   ├── __init__.py
│   ├── base.py           # Abstract adapter interface
│   └── newcastle.py      # Newcastle portal adapter
├── storage/              # SQLite persistence
│   ├── __init__.py
│   ├── models.py         # Data models
│   └── database.py       # Database operations
└── qc/                   # Quality Control
    ├── __init__.py       # Module exports and default refs
    ├── scorer.py         # Scoring rules (exact/partial/miss)
    ├── report.py         # QC report generation
    └── benchmark.py      # End-to-end benchmark runner
```

## Running Tests

```bash
# Install dev dependencies
pip install -e '.[dev]'

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_plana.py -v
pytest tests/test_cli.py -v
pytest tests/test_qc.py -v
```

## Requirements

- Python 3.11+
- No external API keys required
- SQLite database (created automatically)

### Optional Dependencies

```bash
# Live portal access
pip install -e '.[live]'    # httpx, beautifulsoup4, lxml

# API server
pip install -e '.[api]'     # fastapi, uvicorn

# Development
pip install -e '.[dev]'     # pytest, pytest-asyncio

# All features
pip install -e '.[all]'
```

## Architecture Notes

The system is designed for later extension:

- **Policy Extraction**: Can extract from real PDFs when placed at configured paths
- **Similarity Search**: Interface supports future vector-based search
- **Document Management**: Interface supports live portal document download
- **Report Generation**: Template-based, can be enhanced with LLM integration

## License

MIT License - see [LICENSE](LICENSE) for details.
