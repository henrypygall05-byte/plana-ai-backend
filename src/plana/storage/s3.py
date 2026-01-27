"""
S3-compatible storage backend.

Stores documents in S3 or S3-compatible object storage (MinIO, etc.).
Suitable for production deployments.
"""

from typing import AsyncIterator

import aioboto3
import structlog
from botocore.exceptions import ClientError

from plana.config import get_settings
from plana.storage.base import StorageBackend

logger = structlog.get_logger(__name__)


class S3StorageBackend(StorageBackend):
    """
    S3-compatible object storage backend.

    Supports AWS S3 and S3-compatible services like MinIO.
    """

    def __init__(
        self,
        bucket: str,
        region: str = "eu-west-2",
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
    ):
        """Initialize S3 storage.

        Args:
            bucket: S3 bucket name
            region: AWS region
            endpoint_url: Custom endpoint URL (for S3-compatible services)
            access_key: AWS access key (or from environment)
            secret_key: AWS secret key (or from environment)
        """
        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self._session = aioboto3.Session()

    def _get_client_config(self) -> dict:
        """Get boto3 client configuration."""
        config = {
            "region_name": self.region,
        }
        if self.endpoint_url:
            config["endpoint_url"] = self.endpoint_url
        if self.access_key and self.secret_key:
            config["aws_access_key_id"] = self.access_key
            config["aws_secret_access_key"] = self.secret_key
        return config

    async def save(
        self,
        key: str,
        content: bytes | AsyncIterator[bytes],
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Save content to S3."""
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if metadata:
            extra_args["Metadata"] = metadata

        async with self._session.client("s3", **self._get_client_config()) as s3:
            if isinstance(content, bytes):
                await s3.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=content,
                    **extra_args,
                )
            else:
                # For streaming, collect chunks
                chunks = []
                async for chunk in content:
                    chunks.append(chunk)
                body = b"".join(chunks)
                await s3.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=body,
                    **extra_args,
                )

        logger.debug("Saved to S3", key=key, bucket=self.bucket)
        return f"s3://{self.bucket}/{key}"

    async def load(self, key: str) -> bytes:
        """Load content from S3."""
        async with self._session.client("s3", **self._get_client_config()) as s3:
            try:
                response = await s3.get_object(Bucket=self.bucket, Key=key)
                async with response["Body"] as stream:
                    return await stream.read()
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey":
                    raise FileNotFoundError(f"Key not found: {key}")
                raise

    async def load_stream(self, key: str) -> AsyncIterator[bytes]:
        """Load content as async stream."""
        async with self._session.client("s3", **self._get_client_config()) as s3:
            try:
                response = await s3.get_object(Bucket=self.bucket, Key=key)
                async with response["Body"] as stream:
                    async for chunk in stream.iter_chunks():
                        yield chunk
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey":
                    raise FileNotFoundError(f"Key not found: {key}")
                raise

    async def exists(self, key: str) -> bool:
        """Check if key exists in S3."""
        async with self._session.client("s3", **self._get_client_config()) as s3:
            try:
                await s3.head_object(Bucket=self.bucket, Key=key)
                return True
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    return False
                raise

    async def delete(self, key: str) -> bool:
        """Delete object from S3."""
        async with self._session.client("s3", **self._get_client_config()) as s3:
            try:
                await s3.delete_object(Bucket=self.bucket, Key=key)
                return True
            except ClientError:
                return False

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys with prefix."""
        keys = []
        async with self._session.client("s3", **self._get_client_config()) as s3:
            paginator = s3.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    keys.append(obj["Key"])
        return keys

    async def get_metadata(self, key: str) -> dict[str, str]:
        """Get metadata for S3 object."""
        async with self._session.client("s3", **self._get_client_config()) as s3:
            try:
                response = await s3.head_object(Bucket=self.bucket, Key=key)
                return response.get("Metadata", {})
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    raise FileNotFoundError(f"Key not found: {key}")
                raise

    async def get_size(self, key: str) -> int:
        """Get object size in bytes."""
        async with self._session.client("s3", **self._get_client_config()) as s3:
            try:
                response = await s3.head_object(Bucket=self.bucket, Key=key)
                return response["ContentLength"]
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    raise FileNotFoundError(f"Key not found: {key}")
                raise

    def get_public_url(self, key: str) -> str | None:
        """Get public URL for S3 object."""
        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket}/{key}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
