web: uvicorn plana.api.app:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --workers 1
worker: python -m plana.documents.worker --loop --interval 2
