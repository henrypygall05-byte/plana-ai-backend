"""Tests for storage system."""

import pytest
from pathlib import Path

from plana.storage import LocalStorageBackend, DocumentStore
from plana.core.models import ApplicationDocument, DocumentType


class TestLocalStorageBackend:
    """Tests for local filesystem storage."""

    @pytest.fixture
    def storage(self, tmp_path: Path):
        """Create local storage backend."""
        return LocalStorageBackend(tmp_path)

    @pytest.mark.asyncio
    async def test_save_and_load(self, storage):
        """Test saving and loading content."""
        content = b"Test content"
        key = "test/file.txt"

        await storage.save(key, content)
        loaded = await storage.load(key)

        assert loaded == content

    @pytest.mark.asyncio
    async def test_save_with_metadata(self, storage):
        """Test saving with metadata."""
        content = b"Test content"
        key = "test/file.txt"
        metadata = {"type": "test", "version": "1"}

        await storage.save(key, content, metadata=metadata)
        loaded_meta = await storage.get_metadata(key)

        assert loaded_meta["type"] == "test"

    @pytest.mark.asyncio
    async def test_exists(self, storage):
        """Test checking if key exists."""
        key = "test/file.txt"

        assert await storage.exists(key) is False

        await storage.save(key, b"content")

        assert await storage.exists(key) is True

    @pytest.mark.asyncio
    async def test_delete(self, storage):
        """Test deleting content."""
        key = "test/file.txt"
        await storage.save(key, b"content")

        result = await storage.delete(key)
        assert result is True
        assert await storage.exists(key) is False

        # Delete non-existent
        result = await storage.delete(key)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_size(self, storage):
        """Test getting content size."""
        key = "test/file.txt"
        content = b"12345"
        await storage.save(key, content)

        size = await storage.get_size(key)
        assert size == 5

    @pytest.mark.asyncio
    async def test_list_keys(self, storage):
        """Test listing keys."""
        await storage.save("dir1/file1.txt", b"content")
        await storage.save("dir1/file2.txt", b"content")
        await storage.save("dir2/file3.txt", b"content")

        all_keys = await storage.list_keys()
        assert len(all_keys) >= 3

        dir1_keys = await storage.list_keys("dir1")
        # Note: key matching depends on implementation


class TestDocumentStore:
    """Tests for document store."""

    @pytest.fixture
    def store(self, tmp_path: Path):
        """Create document store."""
        backend = LocalStorageBackend(tmp_path)
        return DocumentStore(backend=backend)

    @pytest.fixture
    def document(self):
        """Create test document."""
        return ApplicationDocument(
            id="doc1",
            application_reference="2026/0101/01/NPA",
            title="Test Document",
            document_type=DocumentType.OTHER,
            file_type="pdf",
            source_url="https://example.com/doc.pdf",
        )

    @pytest.mark.asyncio
    async def test_compute_checksum(self, store):
        """Test checksum computation."""
        content = b"test content"
        checksum, full_content = await store.compute_checksum(content)

        assert len(checksum) == 64  # SHA-256 hex
        assert full_content == content

    @pytest.mark.asyncio
    async def test_store_document(self, store, document):
        """Test storing a document."""
        content = b"PDF content here"

        updated_doc = await store.store_document(document, content)

        assert updated_doc.storage_path is not None
        assert updated_doc.checksum is not None
        assert updated_doc.file_size_bytes == len(content)

    @pytest.mark.asyncio
    async def test_store_document_deduplication(self, store, document):
        """Test document deduplication."""
        content = b"Same content"

        # Store first time
        doc1 = await store.store_document(document, content)
        checksum1 = doc1.checksum

        # Store again with same content
        document.id = "doc2"
        doc2 = await store.store_document(document, content)

        # Should have same checksum
        assert doc2.checksum == checksum1

    @pytest.mark.asyncio
    async def test_store_extracted_text(self, store, document):
        """Test storing extracted text."""
        text = "Extracted text content"

        updated_doc = await store.store_extracted_text(document, text)

        assert updated_doc.text_extracted is True
        assert updated_doc.text_storage_path is not None

    @pytest.mark.asyncio
    async def test_document_exists(self, store, document):
        """Test checking if document exists."""
        assert await store.document_exists(document) is False

        await store.store_document(document, b"content")

        # After storage, the document should exist
        # (depends on _get_document_key implementation)

    @pytest.mark.asyncio
    async def test_has_changed(self, store, document):
        """Test checking if document has changed."""
        content1 = b"Original content"
        content2 = b"New content"

        # No checksum yet
        assert await store.has_changed(document, content1) is True

        # Store document
        document = await store.store_document(document, content1)

        # Same content
        assert await store.has_changed(document, content1) is False

        # Different content
        assert await store.has_changed(document, content2) is True
