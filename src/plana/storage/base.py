"""
Abstract storage backend interface.

Defines the contract that all storage implementations must follow.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncIterator


class StorageBackend(ABC):
    """
    Abstract base class for document storage backends.

    All storage backends must implement these methods to support
    document storage, retrieval, and management.
    """

    @abstractmethod
    async def save(
        self,
        key: str,
        content: bytes | AsyncIterator[bytes],
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Save content to storage.

        Args:
            key: Storage key/path for the content
            content: Content as bytes or async iterator of chunks
            content_type: MIME type of content
            metadata: Optional metadata to store with content

        Returns:
            The final storage path/key
        """
        pass

    @abstractmethod
    async def load(self, key: str) -> bytes:
        """Load content from storage.

        Args:
            key: Storage key/path

        Returns:
            Content as bytes

        Raises:
            FileNotFoundError: If key doesn't exist
        """
        pass

    @abstractmethod
    async def load_stream(self, key: str) -> AsyncIterator[bytes]:
        """Load content as async stream.

        Args:
            key: Storage key/path

        Yields:
            Chunks of content

        Raises:
            FileNotFoundError: If key doesn't exist
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in storage.

        Args:
            key: Storage key/path

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete content from storage.

        Args:
            key: Storage key/path

        Returns:
            True if deleted, False if didn't exist
        """
        pass

    @abstractmethod
    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys with given prefix.

        Args:
            prefix: Key prefix to filter by

        Returns:
            List of matching keys
        """
        pass

    @abstractmethod
    async def get_metadata(self, key: str) -> dict[str, str]:
        """Get metadata for a stored object.

        Args:
            key: Storage key/path

        Returns:
            Metadata dictionary

        Raises:
            FileNotFoundError: If key doesn't exist
        """
        pass

    @abstractmethod
    async def get_size(self, key: str) -> int:
        """Get size of stored content in bytes.

        Args:
            key: Storage key/path

        Returns:
            Size in bytes

        Raises:
            FileNotFoundError: If key doesn't exist
        """
        pass

    @abstractmethod
    def get_public_url(self, key: str) -> str | None:
        """Get public URL for content if available.

        Args:
            key: Storage key/path

        Returns:
            Public URL or None if not applicable
        """
        pass
