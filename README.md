# Plana.AI Backend

AI-powered planning intelligence platform for UK planning applications. Generates structured case officer-style planning reports with policy citations, similar case analysis, and recommendations.

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install package
pip install -e .

# Initialize the system
plana init

# List available demo applications
plana demo

# Process an application and generate a report
plana process 2024/0930/01/DET --output report.md
```

## Features

- **Policy Retrieval**: Retrieves relevant policies from NPPF, Core Strategy (CSUCP), and Development Allocations Plan (DAP) with page citations
- **Similar Case Search**: Finds similar historic planning applications for precedent analysis
- **Report Generation**: Creates structured Markdown reports with all required sections
- **Offline-First**: Works entirely offline with demo data - no API keys or external services required

## Available Commands

```bash
plana --help                              # Show help
plana init                                # Initialize the system
plana demo                                # List available demo applications
plana process <ref>                       # Process application (console output)
plana process <ref> --output report.md    # Process and save report to file
plana report <ref> --output report.md     # Generate report only
```

## Demo Applications

| Reference | Description | Constraints |
|-----------|-------------|-------------|
| `2024/0930/01/DET` | T J Hughes extension | Conservation Area, Listed Buildings |
| `2024/0943/01/LBC` | T J Hughes listed building consent | Listed Building, Conservation Area |
| `2024/0300/01/LBC` | Grainger Street shopfront | Listed Building, Conservation Area |
| `2025/0015/01/DET` | Town Moor drainage | Town Moor, Flood Zone 2 |
| `2023/1500/01/HOU` | Jesmond Road householder | None |

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
└── report/               # Report generation
    ├── __init__.py
    └── generator.py      # Markdown report generator
```

## Running Tests

```bash
pip install pytest
pytest tests/test_plana.py -v
```

## Requirements

- Python 3.11+
- No external API keys required
- No database required

## Architecture Notes

The system is designed for later extension:

- **Policy Extraction**: Can extract from real PDFs when placed at configured paths
- **Similarity Search**: Interface supports future vector-based search
- **Document Management**: Interface supports live portal document download
- **Report Generation**: Template-based, can be enhanced with LLM integration

## License

MIT License - see [LICENSE](LICENSE) for details.
