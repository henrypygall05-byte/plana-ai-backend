"""
Document storage and management system.

Provides pluggable storage backends (local filesystem, S3) for documents
and extracted text.
"""

from plana.storage.base import StorageBackend
from plana.storage.local import LocalStorageBackend

# Lazy imports for optional backends
def get_s3_backend():
    """Get S3 backend (requires aioboto3)."""
    from plana.storage.s3 import S3StorageBackend
    return S3StorageBackend

def get_document_store():
    """Get DocumentStore class."""
    from plana.storage.document_store import DocumentStore
    return DocumentStore

# For backwards compatibility, expose DocumentStore directly
# but delay the import
class _LazyDocumentStore:
    """Lazy wrapper for DocumentStore to avoid import-time S3 dependency."""
    _cls = None

    def __new__(cls, *args, **kwargs):
        if cls._cls is None:
            from plana.storage.document_store import DocumentStore
            cls._cls = DocumentStore
        return cls._cls(*args, **kwargs)

DocumentStore = _LazyDocumentStore

__all__ = [
    "StorageBackend",
    "LocalStorageBackend",
    "DocumentStore",
    "get_s3_backend",
    "get_document_store",
]
