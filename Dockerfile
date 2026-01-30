FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Copy the repo into the container
COPY . /app

# Force "src/" layout imports
ENV PYTHONPATH=/app/src

# Install runtime deps only (avoid editable install issues on Render)
RUN pip install --upgrade pip \
 && pip install "uvicorn[standard]" fastapi "pydantic>=2"

# Prevent top-level /app/plana from shadowing /app/src/plana
RUN rm -rf /app/plana || true

CMD ["sh", "-c", "uvicorn \"plana.api.app:create_app\" --factory --host 0.0.0.0 --port ${PORT:-8000}"]
