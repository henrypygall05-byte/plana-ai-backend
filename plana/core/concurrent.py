"""
Concurrent utilities for Plana.AI.

Provides utilities for concurrent operations like parallel downloads.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Generic, Optional, TypeVar

from plana.core.constants import DocumentConfig
from plana.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class TaskResult(Generic[T]):
    """Result of an async task."""

    success: bool
    value: Optional[T] = None
    error: Optional[str] = None
    item_id: Optional[str] = None


async def run_with_semaphore(
    semaphore: asyncio.Semaphore,
    coro: Awaitable[T],
    item_id: Optional[str] = None,
) -> TaskResult[T]:
    """Run a coroutine with semaphore control.

    Args:
        semaphore: Semaphore to control concurrency
        coro: Coroutine to run
        item_id: Optional identifier for logging

    Returns:
        TaskResult with success/failure info
    """
    async with semaphore:
        try:
            result = await coro
            return TaskResult(success=True, value=result, item_id=item_id)
        except Exception as e:
            logger.warning(
                "concurrent_task_failed",
                item_id=item_id,
                error=str(e),
            )
            return TaskResult(success=False, error=str(e), item_id=item_id)


async def run_concurrent(
    items: list[T],
    async_func: Callable[[T], Awaitable[R]],
    max_concurrent: int = DocumentConfig.MAX_CONCURRENT_DOWNLOADS,
    get_item_id: Optional[Callable[[T], str]] = None,
) -> list[TaskResult[R]]:
    """Run async function on multiple items concurrently.

    Args:
        items: List of items to process
        async_func: Async function to apply to each item
        max_concurrent: Maximum concurrent operations
        get_item_id: Optional function to get item ID for logging

    Returns:
        List of TaskResults in same order as input items
    """
    if not items:
        return []

    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_item(item: T, index: int) -> tuple[int, TaskResult[R]]:
        item_id = get_item_id(item) if get_item_id else str(index)
        result = await run_with_semaphore(
            semaphore,
            async_func(item),
            item_id=item_id,
        )
        return index, result

    # Create tasks
    tasks = [process_item(item, i) for i, item in enumerate(items)]

    # Run concurrently
    indexed_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Sort by original index and extract results
    results: list[TaskResult[R]] = [None] * len(items)  # type: ignore
    for indexed_result in indexed_results:
        if isinstance(indexed_result, Exception):
            # Handle gather exception
            logger.error("concurrent_gather_exception", error=str(indexed_result))
            continue
        index, result = indexed_result
        results[index] = result

    # Fill any missing results
    for i in range(len(results)):
        if results[i] is None:
            results[i] = TaskResult(success=False, error="Task did not complete")

    return results


@dataclass
class BatchProgress:
    """Progress tracking for batch operations."""

    total: int
    completed: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0

    @property
    def pending(self) -> int:
        """Number of items still pending."""
        return self.total - self.completed

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.completed == 0:
            return 0.0
        return (self.succeeded / self.completed) * 100

    def record_success(self) -> None:
        """Record a successful completion."""
        self.completed += 1
        self.succeeded += 1

    def record_failure(self) -> None:
        """Record a failed completion."""
        self.completed += 1
        self.failed += 1

    def record_skip(self) -> None:
        """Record a skipped item."""
        self.completed += 1
        self.skipped += 1


class ConcurrentDownloader:
    """Handles concurrent document downloads with progress tracking."""

    def __init__(
        self,
        max_concurrent: int = DocumentConfig.MAX_CONCURRENT_DOWNLOADS,
    ):
        """Initialize the downloader.

        Args:
            max_concurrent: Maximum concurrent downloads
        """
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def download_documents(
        self,
        documents: list[Any],
        download_func: Callable[[Any], Awaitable[Optional[str]]],
        should_skip: Optional[Callable[[Any], bool]] = None,
    ) -> tuple[BatchProgress, list[TaskResult[str]]]:
        """Download multiple documents concurrently.

        Args:
            documents: List of document objects
            download_func: Async function to download a document (returns path or None)
            should_skip: Optional function to check if document should be skipped

        Returns:
            Tuple of (progress, results)
        """
        progress = BatchProgress(total=len(documents))
        results: list[TaskResult[str]] = []

        if not documents:
            return progress, results

        async def process_document(
            doc: Any, index: int
        ) -> tuple[int, TaskResult[str]]:
            # Check if should skip
            if should_skip and should_skip(doc):
                progress.record_skip()
                return index, TaskResult(
                    success=True,
                    value=None,
                    item_id=str(index),
                )

            # Download with semaphore
            async with self._semaphore:
                try:
                    path = await download_func(doc)
                    if path:
                        progress.record_success()
                        return index, TaskResult(
                            success=True,
                            value=path,
                            item_id=str(index),
                        )
                    else:
                        progress.record_failure()
                        return index, TaskResult(
                            success=False,
                            error="Download returned None",
                            item_id=str(index),
                        )
                except Exception as e:
                    progress.record_failure()
                    return index, TaskResult(
                        success=False,
                        error=str(e),
                        item_id=str(index),
                    )

        # Create tasks
        tasks = [process_document(doc, i) for i, doc in enumerate(documents)]

        # Run concurrently
        indexed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        results = [None] * len(documents)  # type: ignore
        for indexed_result in indexed_results:
            if isinstance(indexed_result, Exception):
                logger.error("download_exception", error=str(indexed_result))
                continue
            index, result = indexed_result
            results[index] = result

        # Fill missing
        for i in range(len(results)):
            if results[i] is None:
                results[i] = TaskResult(success=False, error="Task did not complete")

        return progress, results


async def download_with_retry(
    download_func: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    backoff_multiplier: float = 2.0,
    initial_delay: float = 1.0,
) -> TaskResult[T]:
    """Download with exponential backoff retry.

    Args:
        download_func: Async function to call
        max_retries: Maximum retry attempts
        backoff_multiplier: Backoff multiplier
        initial_delay: Initial delay in seconds

    Returns:
        TaskResult with success/failure info
    """
    last_error = None
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            result = await download_func()
            return TaskResult(success=True, value=result)
        except Exception as e:
            last_error = str(e)
            logger.warning(
                "download_retry",
                attempt=attempt + 1,
                max_retries=max_retries,
                error=last_error,
            )

            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= backoff_multiplier

    return TaskResult(success=False, error=last_error)
