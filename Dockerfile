FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY . /app

ENV PYTHONPATH=/app/src

RUN pip install --upgrade pip \
 && pip install -e . \
 && pip install "uvicorn[standard]" fastapi "pydantic>=2"

CMD ["sh", "-c", "uvicorn \"plana.api.app:create_app\" --factory --host 0.0.0.0 --port ${PORT:-8000}"]
