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
└── storage/              # SQLite persistence
    ├── __init__.py
    ├── models.py         # Data models
    └── database.py       # Database operations
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
