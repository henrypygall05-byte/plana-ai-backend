# Plana.AI Backend

AI-powered planning intelligence platform for UK planning applications. Plana.AI retrieves, analyses, and reasons over planning applications to generate structured, case officer-style planning reports.

## Overview

Plana.AI is an entirely automated system that processes planning applications end-to-end:

1. **Fetch** application data from council planning portals
2. **Download** and store all submitted documents
3. **Extract** text from PDFs and other documents
4. **Index** content for semantic search
5. **Retrieve** relevant planning policies (NPPF, Local Plan)
6. **Find** similar historic cases for precedent
7. **Generate** case officer-style assessment reports
8. **Learn** from feedback to continuously improve

## Pilot Scope

This pilot is limited to **Newcastle City Council**. The system is architected to scale to additional councils without major rewrites.

## Quick Start (Local Development)

Get up and running in **under 2 minutes** with zero external dependencies.

### Prerequisites

- Python 3.11+ (that's it!)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/plana-ai-backend.git
cd plana-ai-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install core dependencies only (no S3, no ML, no DB)
pip install -e .

# Initialize the system
plana init

# See available demo applications
plana demo

# Process your first application!
plana process 2024/0930/01/DET
```

That's it! No API keys, no database, no Redis required.

### What Works Out of the Box

- ✅ Full pipeline execution with demo applications
- ✅ Document processing and text extraction
- ✅ Policy retrieval (keyword-based)
- ✅ Similar case search (keyword-based)
- ✅ Report generation (template-based)
- ✅ REST API server

### Optional: Enable AI-Powered Reports

To get real AI-generated reports:

```bash
# Install LLM dependencies
pip install -e ".[llm]"

# Set your API key
export ANTHROPIC_API_KEY=your-key-here
# or
export OPENAI_API_KEY=your-key-here

# Process with real AI
plana process 2024/0930/01/DET
```

### Optional: Full Production Setup

For production with vector search, S3 storage, and database:

```bash
# Install all dependencies
pip install -e ".[all]"

# Configure services
cp .env.example .env
# Edit .env with your configuration

# Use live portal (requires network)
export PLANA_USE_FIXTURES=false
```

### Using Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api
```

## Configuration Modes

| Mode | Use Case | Command |
|------|----------|---------|
| **Fixture + Stub** (default) | Local dev, demos | `plana process <ref>` |
| **Fixture + LLM** | Test AI reports | Set `ANTHROPIC_API_KEY` |
| **Live + Stub** | Test portal fetch | `PLANA_USE_FIXTURES=false` |
| **Live + LLM** | Full production | All keys configured |

Check current configuration:
```bash
plana status
```

## Usage

### Process an Application

```bash
# Process a planning application by reference
plana process 2026/0101/01/NPA

# Force reprocessing
plana process 2026/0101/01/NPA --force
```

### Generate a Report

```bash
# Generate case officer report
plana report 2026/0101/01/NPA

# Save to file
plana report 2026/0101/01/NPA --output report.md
```

### Start API Server

```bash
# Start the API server
plana serve

# With auto-reload for development
plana serve --reload
```

### Search Applications

```bash
# Search by postcode
plana search --postcode NE1

# Search by address
plana search --address "Grey Street"
```

## API Endpoints

### Applications

- `GET /api/v1/applications/{council_id}/{reference}` - Get application details
- `POST /api/v1/applications/search` - Search applications
- `POST /api/v1/applications/process` - Process an application

### Reports

- `POST /api/v1/reports/generate` - Generate a report
- `GET /api/v1/reports/{reference}` - Get generated report
- `GET /api/v1/reports/{reference}/versions` - List report versions

### Policies

- `GET /api/v1/policies` - List policies
- `GET /api/v1/policies/{id}` - Get policy details

### Feedback

- `POST /api/v1/feedback/report` - Submit report feedback
- `POST /api/v1/feedback/similarity` - Submit similarity feedback
- `POST /api/v1/feedback/outcome` - Record decision outcome

### Health

- `GET /health` - Health check
- `GET /ready` - Readiness check

## Architecture

```
src/plana/
├── api/                 # REST API (FastAPI)
│   └── routes/          # API endpoints
├── config/              # Configuration management
├── core/                # Domain models
├── councils/            # Council portal integrations
│   ├── base.py          # Abstract portal interface
│   └── newcastle.py     # Newcastle implementation
├── feedback/            # Feedback and learning system
├── llm/                 # LLM client abstraction
├── pipeline/            # End-to-end orchestration
├── policies/            # Policy management
├── processing/          # Document processing
├── reports/             # Report generation
├── search/              # Vector search and similarity
└── storage/             # Document storage
```

## Key Components

### Council Abstraction (`councils/`)

Each council implements the `CouncilPortal` interface, enabling multi-council support:

```python
from plana.councils import CouncilRegistry

portal = CouncilRegistry.get("newcastle")
application = await portal.fetch_application("2026/0101/01/NPA")
```

### Pipeline Orchestrator (`pipeline/`)

The `PlanaPipeline` class coordinates the entire processing flow:

```python
from plana.pipeline import PlanaPipeline

pipeline = PlanaPipeline()
result = await pipeline.run("2026/0101/01/NPA")

print(result.report.full_content)
```

### Report Generation (`reports/`)

Reports are generated using AI with structured templates:

```python
from plana.reports import ReportGenerator, ReportTemplate

generator = ReportGenerator()
report = await generator.generate_report(
    application=app,
    policies=policies,
    similar_cases=similar_cases,
)
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PLANA_USE_FIXTURES` | Use fixture data instead of live portal | `true` |
| `PLANA_SKIP_LLM` | Skip LLM calls (use templates) | `false` |
| `PLANA_DATA_DIR` | Data storage directory | `~/.plana` |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `OPENAI_API_KEY` | OpenAI API key (alternative) | - |
| `STORAGE_BACKEND` | Storage backend (local/s3) | `local` |
| `VECTOR_STORE_BACKEND` | Vector store (stub/chroma) | `stub` |

### Installation Extras

```bash
pip install -e ".[s3]"       # S3 storage support
pip install -e ".[vectors]"  # ChromaDB + embeddings
pip install -e ".[llm]"      # Anthropic/OpenAI clients
pip install -e ".[ocr]"      # OCR for scanned documents
pip install -e ".[db]"       # PostgreSQL support
pip install -e ".[dev]"      # Development tools
pip install -e ".[all]"      # Everything
```

See `.env.example` for full configuration options.

## Continuous Improvement

The system is designed for continuous learning:

1. **Similarity Feedback** - Track which historic cases were useful
2. **Policy Feedback** - Track which policies were cited in final reports
3. **Report Feedback** - Store edits between AI draft and final report
4. **Outcome Feedback** - Record actual decisions to calibrate predictions

All feedback is stored and used to improve:
- Document classification accuracy
- Similarity search relevance
- Policy retrieval precision
- Report structure and reasoning

## Development

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=plana

# Run specific test file
pytest tests/test_pipeline.py
```

### Code Quality

```bash
# Format code
black src tests

# Lint
ruff check src tests

# Type check
mypy src
```

## License

MIT License - see [LICENSE](LICENSE) for details.
