"""
Caching utilities for Plana.AI.

Provides in-memory caching with TTL support.
For production, this should be extended to use Redis.
"""

import asyncio
import functools
import hashlib
import json
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Generic, Optional, TypeVar

from plana.core.constants import CacheConfig
from plana.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """A cached value with metadata."""

    value: T
    expires_at: float
    created_at: float

    @property
    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        return time.time() > self.expires_at

    @property
    def age_seconds(self) -> float:
        """Get the age of the entry in seconds."""
        return time.time() - self.created_at


class InMemoryCache(Generic[T]):
    """Thread-safe in-memory cache with TTL support.

    Uses a simple dictionary with periodic cleanup.
    For production, consider using Redis.
    """

    def __init__(
        self,
        default_ttl: int = CacheConfig.DEFAULT_TTL,
        max_size: int = CacheConfig.MAX_CACHE_SIZE,
    ):
        """Initialize the cache.

        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of entries
        """
        self._cache: dict[str, CacheEntry[T]] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[T]:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None

            self._hits += 1
            return entry.value

    def set(
        self, key: str, value: T, ttl: Optional[int] = None
    ) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        ttl = ttl if ttl is not None else self.default_ttl
        now = time.time()

        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_oldest()

            self._cache[key] = CacheEntry(
                value=value,
                expires_at=now + ttl,
                created_at=now,
            )

    def delete(self, key: str) -> bool:
        """Delete a key from the cache.

        Args:
            key: Cache key

        Returns:
            True if key existed, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> int:
        """Clear all entries from the cache.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def cleanup(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries removed
        """
        now = time.time()
        removed = 0

        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items() if v.expires_at < now
            ]
            for key in expired_keys:
                del self._cache[key]
                removed += 1

        if removed > 0:
            logger.debug("cache_cleanup", entries_removed=removed)

        return removed

    def _evict_oldest(self) -> None:
        """Evict the oldest entry to make room."""
        if not self._cache:
            return

        oldest_key = min(
            self._cache.keys(), key=lambda k: self._cache[k].created_at
        )
        del self._cache[oldest_key]
        logger.debug("cache_eviction", key=oldest_key)

    @property
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    @property
    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
        }


# =============================================================================
# Global Cache Instances
# =============================================================================

_policy_cache: Optional[InMemoryCache] = None
_similarity_cache: Optional[InMemoryCache] = None


def get_policy_cache() -> InMemoryCache:
    """Get the global policy cache."""
    global _policy_cache
    if _policy_cache is None:
        _policy_cache = InMemoryCache(
            default_ttl=CacheConfig.POLICY_CACHE_TTL,
            max_size=500,
        )
    return _policy_cache


def get_similarity_cache() -> InMemoryCache:
    """Get the global similarity cache."""
    global _similarity_cache
    if _similarity_cache is None:
        _similarity_cache = InMemoryCache(
            default_ttl=CacheConfig.DEFAULT_TTL,
            max_size=200,
        )
    return _similarity_cache


# =============================================================================
# Caching Decorators
# =============================================================================


def make_cache_key(*args, **kwargs) -> str:
    """Create a cache key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Hash-based cache key
    """
    # Create a string representation of args and kwargs
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)

    # Hash for consistent key length
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(
    ttl: int = CacheConfig.DEFAULT_TTL,
    cache: Optional[InMemoryCache] = None,
    key_prefix: str = "",
) -> Callable:
    """Decorator to cache function results.

    Args:
        ttl: Time-to-live in seconds
        cache: Cache instance to use (creates new one if not specified)
        key_prefix: Prefix for cache keys

    Returns:
        Decorator function
    """
    _cache = cache or InMemoryCache(default_ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            cache_key = f"{key_prefix}:{func.__name__}:{make_cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                logger.debug("cache_hit", function=func.__name__, key=cache_key[:20])
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl)
            logger.debug("cache_miss", function=func.__name__, key=cache_key[:20])

            return result

        return wrapper

    return decorator


def async_cached(
    ttl: int = CacheConfig.DEFAULT_TTL,
    cache: Optional[InMemoryCache] = None,
    key_prefix: str = "",
) -> Callable:
    """Decorator to cache async function results.

    Args:
        ttl: Time-to-live in seconds
        cache: Cache instance to use
        key_prefix: Prefix for cache keys

    Returns:
        Decorator function
    """
    _cache = cache or InMemoryCache(default_ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            cache_key = f"{key_prefix}:{func.__name__}:{make_cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                logger.debug("cache_hit", function=func.__name__, key=cache_key[:20])
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            _cache.set(cache_key, result, ttl)
            logger.debug("cache_miss", function=func.__name__, key=cache_key[:20])

            return result

        return wrapper

    return decorator


# =============================================================================
# Cache Invalidation
# =============================================================================


def invalidate_policy_cache() -> int:
    """Invalidate all policy cache entries.

    Returns:
        Number of entries cleared
    """
    cache = get_policy_cache()
    count = cache.clear()
    logger.info("policy_cache_invalidated", entries_cleared=count)
    return count


def invalidate_similarity_cache() -> int:
    """Invalidate all similarity cache entries.

    Returns:
        Number of entries cleared
    """
    cache = get_similarity_cache()
    count = cache.clear()
    logger.info("similarity_cache_invalidated", entries_cleared=count)
    return count
