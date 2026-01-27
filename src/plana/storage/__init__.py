"""
Document storage and management system.

Provides pluggable storage backends (local filesystem, S3) for documents
and extracted text.
"""

from plana.storage.base import StorageBackend
from plana.storage.document_store import DocumentStore
from plana.storage.local import LocalStorageBackend
from plana.storage.s3 import S3StorageBackend

__all__ = [
    "StorageBackend",
    "DocumentStore",
    "LocalStorageBackend",
    "S3StorageBackend",
]
