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

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Anthropic API key (or OpenAI)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/plana-ai-backend.git
cd plana-ai-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev]"

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys and settings

# Initialize the system
plana init
```

### Using Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api
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

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (anthropic/openai) | anthropic |
| `LLM_ANTHROPIC_API_KEY` | Anthropic API key | - |
| `STORAGE_BACKEND` | Storage backend (local/s3) | local |
| `DATABASE_URL` | PostgreSQL connection URL | - |
| `REDIS_URL` | Redis connection URL | - |

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
