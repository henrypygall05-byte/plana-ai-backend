"""
Local filesystem storage backend.

Stores documents and extracted text on the local filesystem.
Suitable for development and pilot phase.
"""

import asyncio
import json
from pathlib import Path
from typing import AsyncIterator

import aiofiles
import aiofiles.os
import structlog

from plana.storage.base import StorageBackend

logger = structlog.get_logger(__name__)


class LocalStorageBackend(StorageBackend):
    """
    Local filesystem storage backend.

    Stores files in a directory structure:
    - base_path/
      - documents/
        - {council_id}/
          - {application_ref}/
            - {document_id}.{ext}
      - text/
        - {council_id}/
          - {application_ref}/
            - {document_id}.txt
      - metadata/
        - {key}.json
    """

    def __init__(self, base_path: Path):
        """Initialize local storage.

        Args:
            base_path: Root directory for storage
        """
        self.base_path = Path(base_path)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create required directories."""
        for subdir in ["documents", "text", "metadata"]:
            (self.base_path / subdir).mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, key: str) -> Path:
        """Get full filesystem path for key."""
        # Sanitize key to prevent path traversal
        safe_key = key.replace("..", "").lstrip("/")
        return self.base_path / safe_key

    def _get_metadata_path(self, key: str) -> Path:
        """Get path for metadata file."""
        safe_key = key.replace("/", "_").replace("..", "")
        return self.base_path / "metadata" / f"{safe_key}.json"

    async def save(
        self,
        key: str,
        content: bytes | AsyncIterator[bytes],
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Save content to local filesystem."""
        path = self._get_full_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            async with aiofiles.open(path, "wb") as f:
                await f.write(content)
        else:
            async with aiofiles.open(path, "wb") as f:
                async for chunk in content:
                    await f.write(chunk)

        # Save metadata
        meta = metadata or {}
        if content_type:
            meta["content_type"] = content_type

        if meta:
            meta_path = self._get_metadata_path(key)
            async with aiofiles.open(meta_path, "w") as f:
                await f.write(json.dumps(meta))

        logger.debug("Saved file", key=key, path=str(path))
        return str(path)

    async def load(self, key: str) -> bytes:
        """Load content from filesystem."""
        path = self._get_full_path(key)

        if not path.exists():
            raise FileNotFoundError(f"Key not found: {key}")

        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def load_stream(self, key: str) -> AsyncIterator[bytes]:
        """Load content as async stream."""
        path = self._get_full_path(key)

        if not path.exists():
            raise FileNotFoundError(f"Key not found: {key}")

        async with aiofiles.open(path, "rb") as f:
            while chunk := await f.read(8192):
                yield chunk

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        path = self._get_full_path(key)
        return path.exists()

    async def delete(self, key: str) -> bool:
        """Delete file from storage."""
        path = self._get_full_path(key)

        if not path.exists():
            return False

        await aiofiles.os.remove(path)

        # Also delete metadata
        meta_path = self._get_metadata_path(key)
        if meta_path.exists():
            await aiofiles.os.remove(meta_path)

        return True

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys with prefix."""
        base = self._get_full_path(prefix) if prefix else self.base_path
        keys = []

        if not base.exists():
            return keys

        def _scan_dir(directory: Path, rel_prefix: str) -> list[str]:
            result = []
            for item in directory.iterdir():
                rel_path = f"{rel_prefix}/{item.name}" if rel_prefix else item.name
                if item.is_file() and not item.suffix == ".json":
                    result.append(rel_path)
                elif item.is_dir() and item.name != "metadata":
                    result.extend(_scan_dir(item, rel_path))
            return result

        # Run synchronous directory scan in thread pool
        loop = asyncio.get_event_loop()
        keys = await loop.run_in_executor(None, _scan_dir, base, prefix)

        return keys

    async def get_metadata(self, key: str) -> dict[str, str]:
        """Get metadata for stored object."""
        meta_path = self._get_metadata_path(key)

        if not meta_path.exists():
            # Return basic metadata from file
            path = self._get_full_path(key)
            if not path.exists():
                raise FileNotFoundError(f"Key not found: {key}")
            return {}

        async with aiofiles.open(meta_path, "r") as f:
            content = await f.read()
            return json.loads(content)

    async def get_size(self, key: str) -> int:
        """Get file size in bytes."""
        path = self._get_full_path(key)

        if not path.exists():
            raise FileNotFoundError(f"Key not found: {key}")

        stat = await aiofiles.os.stat(path)
        return stat.st_size

    def get_public_url(self, key: str) -> str | None:
        """Local storage has no public URLs."""
        return None
