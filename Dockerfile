# Plana.AI Backend Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY pyproject.toml .
COPY src/ src/

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Create data directories
RUN mkdir -p /app/data/documents /app/data/chroma /app/data/feedback /app/data/policies /app/data/results

# Create non-root user
RUN useradd -m -u 1000 plana && \
    chown -R plana:plana /app

USER plana

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "plana.api.app:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
