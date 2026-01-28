"""
High-level document storage and management.

Provides a unified interface for storing, retrieving, and managing
planning documents with deduplication and text extraction support.
"""

import hashlib
from datetime import datetime
from typing import AsyncIterator

import structlog

from plana.config import get_settings
from plana.core.models import ApplicationDocument
from plana.storage.base import StorageBackend
from plana.storage.local import LocalStorageBackend

# S3StorageBackend is imported lazily only when s3 backend is configured
# This allows the app to run without aioboto3 installed

logger = structlog.get_logger(__name__)


class DocumentStore:
    """
    High-level document storage manager.

    Handles document storage, deduplication via checksums,
    and coordination with text extraction.
    """

    def __init__(self, backend: StorageBackend | None = None):
        """Initialize document store.

        Args:
            backend: Storage backend to use. If None, creates from settings.
        """
        self.backend = backend or self._create_backend_from_settings()
        self.settings = get_settings()

    def _create_backend_from_settings(self) -> StorageBackend:
        """Create appropriate backend from settings."""
        settings = get_settings()

        if settings.storage.backend == "s3":
            # Lazy import S3 backend only when needed
            try:
                from plana.storage.s3 import S3StorageBackend
            except ImportError as e:
                raise ImportError(
                    "S3 storage requires aioboto3. Install with: pip install plana-ai-backend[s3]"
                ) from e

            return S3StorageBackend(
                bucket=settings.storage.s3_bucket or "plana-documents",
                region=settings.storage.s3_region,
                endpoint_url=settings.storage.s3_endpoint_url,
                access_key=(
                    settings.storage.s3_access_key.get_secret_value()
                    if settings.storage.s3_access_key
                    else None
                ),
                secret_key=(
                    settings.storage.s3_secret_key.get_secret_value()
                    if settings.storage.s3_secret_key
                    else None
                ),
            )
        else:
            return LocalStorageBackend(settings.storage.local_path)

    def _get_document_key(self, document: ApplicationDocument) -> str:
        """Generate storage key for a document."""
        # Structure: documents/{council_id}/{app_ref}/{doc_id}.{ext}
        parts = document.application_reference.split("/")
        app_ref_safe = "_".join(parts)

        return (
            f"documents/{document.application_reference.split('/')[0]}/"
            f"{app_ref_safe}/{document.id}.{document.file_type}"
        )

    def _get_text_key(self, document: ApplicationDocument) -> str:
        """Generate storage key for extracted text."""
        parts = document.application_reference.split("/")
        app_ref_safe = "_".join(parts)

        return (
            f"text/{document.application_reference.split('/')[0]}/"
            f"{app_ref_safe}/{document.id}.txt"
        )

    async def compute_checksum(
        self, content: bytes | AsyncIterator[bytes]
    ) -> tuple[str, bytes]:
        """Compute SHA-256 checksum of content.

        Args:
            content: Content as bytes or async iterator

        Returns:
            Tuple of (checksum_hex, full_content_bytes)
        """
        hasher = hashlib.sha256()

        if isinstance(content, bytes):
            hasher.update(content)
            return hasher.hexdigest(), content
        else:
            chunks = []
            async for chunk in content:
                hasher.update(chunk)
                chunks.append(chunk)
            full_content = b"".join(chunks)
            return hasher.hexdigest(), full_content

    async def store_document(
        self,
        document: ApplicationDocument,
        content: bytes | AsyncIterator[bytes],
        skip_if_exists: bool = True,
    ) -> ApplicationDocument:
        """Store a document and update its metadata.

        Args:
            document: Document metadata
            content: Document content
            skip_if_exists: Skip if document with same checksum exists

        Returns:
            Updated document with storage path and checksum
        """
        # Compute checksum and get full content
        checksum, full_content = await self.compute_checksum(content)

        key = self._get_document_key(document)

        # Check for duplicate
        if skip_if_exists and await self.backend.exists(key):
            existing_meta = await self.backend.get_metadata(key)
            if existing_meta.get("checksum") == checksum:
                logger.debug(
                    "Document already exists with same checksum",
                    doc_id=document.id,
                    checksum=checksum[:8],
                )
                document.storage_path = key
                document.checksum = checksum
                return document

        # Determine content type
        content_type = self._get_content_type(document.file_type)

        # Store document
        storage_path = await self.backend.save(
            key=key,
            content=full_content,
            content_type=content_type,
            metadata={
                "checksum": checksum,
                "application_reference": document.application_reference,
                "document_id": document.id,
                "document_type": document.document_type.value,
            },
        )

        # Update document
        document.storage_path = storage_path
        document.checksum = checksum
        document.file_size_bytes = len(full_content)
        document.downloaded_at = datetime.utcnow()

        logger.info(
            "Stored document",
            doc_id=document.id,
            size_bytes=document.file_size_bytes,
            checksum=checksum[:8],
        )

        return document

    async def store_extracted_text(
        self,
        document: ApplicationDocument,
        text: str,
    ) -> ApplicationDocument:
        """Store extracted text for a document.

        Args:
            document: Document the text was extracted from
            text: Extracted text content

        Returns:
            Updated document with text storage path
        """
        key = self._get_text_key(document)

        await self.backend.save(
            key=key,
            content=text.encode("utf-8"),
            content_type="text/plain; charset=utf-8",
            metadata={
                "document_id": document.id,
                "application_reference": document.application_reference,
            },
        )

        document.text_storage_path = key
        document.text_extracted = True

        logger.debug(
            "Stored extracted text",
            doc_id=document.id,
            text_length=len(text),
        )

        return document

    async def get_document_content(self, document: ApplicationDocument) -> bytes:
        """Get raw document content.

        Args:
            document: Document to retrieve

        Returns:
            Document content as bytes

        Raises:
            FileNotFoundError: If document not stored
        """
        if not document.storage_path:
            raise FileNotFoundError(f"Document {document.id} not stored")

        # Handle both full paths and keys
        key = document.storage_path
        if key.startswith("s3://"):
            key = "/".join(key.split("/")[3:])

        return await self.backend.load(key)

    async def get_extracted_text(self, document: ApplicationDocument) -> str:
        """Get extracted text for a document.

        Args:
            document: Document to get text for

        Returns:
            Extracted text content

        Raises:
            FileNotFoundError: If text not extracted
        """
        if not document.text_storage_path:
            raise FileNotFoundError(f"Text not extracted for document {document.id}")

        key = document.text_storage_path
        if key.startswith("s3://"):
            key = "/".join(key.split("/")[3:])

        content = await self.backend.load(key)
        return content.decode("utf-8")

    async def document_exists(self, document: ApplicationDocument) -> bool:
        """Check if document is stored.

        Args:
            document: Document to check

        Returns:
            True if stored, False otherwise
        """
        key = self._get_document_key(document)
        return await self.backend.exists(key)

    async def has_changed(
        self,
        document: ApplicationDocument,
        new_content: bytes,
    ) -> bool:
        """Check if document content has changed.

        Args:
            document: Document to check
            new_content: New content to compare

        Returns:
            True if content differs from stored version
        """
        if not document.checksum:
            return True

        new_checksum = hashlib.sha256(new_content).hexdigest()
        return new_checksum != document.checksum

    async def list_documents(
        self,
        council_id: str | None = None,
        application_reference: str | None = None,
    ) -> list[str]:
        """List stored document keys.

        Args:
            council_id: Filter by council
            application_reference: Filter by application

        Returns:
            List of document storage keys
        """
        prefix = "documents/"
        if council_id:
            prefix = f"documents/{council_id}/"
        if application_reference:
            app_ref_safe = "_".join(application_reference.split("/"))
            prefix = f"documents/{council_id}/{app_ref_safe}/"

        return await self.backend.list_keys(prefix)

    def _get_content_type(self, file_type: str) -> str:
        """Get MIME type for file extension."""
        types = {
            "pdf": "application/pdf",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "tiff": "image/tiff",
            "tif": "image/tiff",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xls": "application/vnd.ms-excel",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        return types.get(file_type.lower(), "application/octet-stream")
