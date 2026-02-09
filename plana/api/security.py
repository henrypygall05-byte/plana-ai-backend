"""
Security middleware and authentication for Plana.AI API.

Provides:
- API key authentication
- Request validation
- Rate limiting
- CORS configuration
"""

import hashlib
import hmac
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from plana.config import get_settings
from plana.core.constants import RateLimitConfig
from plana.core.exceptions import AuthenticationError, RateLimitError
from plana.core.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# API Key Authentication
# =============================================================================

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass
class APIKeyInfo:
    """Information about an API key."""

    key_id: str
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True
    rate_limit: Optional[int] = None  # Override default rate limit
    allowed_endpoints: Optional[list[str]] = None  # None = all allowed


class APIKeyManager:
    """Manages API key validation and storage.

    In production, this would use a database. For now, we support
    environment-configured keys for simplicity.
    """

    def __init__(self):
        self._keys: dict[str, APIKeyInfo] = {}
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        """Load API keys from settings."""
        settings = get_settings()

        # Load configured API keys
        for key_config in settings.api_keys:
            key_hash = self._hash_key(key_config.key)
            self._keys[key_hash] = APIKeyInfo(
                key_id=key_config.key_id,
                name=key_config.name,
                created_at=datetime.now(),
                is_active=True,
                rate_limit=key_config.rate_limit,
            )

    @staticmethod
    def _hash_key(key: str) -> str:
        """Hash an API key for secure comparison."""
        return hashlib.sha256(key.encode()).hexdigest()

    def validate_key(self, key: str) -> Optional[APIKeyInfo]:
        """Validate an API key and return its info.

        Args:
            key: The API key to validate

        Returns:
            APIKeyInfo if valid, None if invalid
        """
        key_hash = self._hash_key(key)
        key_info = self._keys.get(key_hash)

        if key_info and key_info.is_active:
            key_info.last_used = datetime.now()
            return key_info

        return None

    @staticmethod
    def generate_key() -> str:
        """Generate a new secure API key.

        Returns:
            A new API key (prefix + random token)
        """
        prefix = "plana"
        token = secrets.token_urlsafe(32)
        return f"{prefix}_{token}"


# Global key manager instance
_key_manager: Optional[APIKeyManager] = None


def get_key_manager() -> APIKeyManager:
    """Get the global API key manager."""
    global _key_manager
    if _key_manager is None:
        _key_manager = APIKeyManager()
    return _key_manager


async def verify_api_key(
    api_key: Optional[str] = Security(API_KEY_HEADER),
) -> Optional[APIKeyInfo]:
    """Dependency to verify API key.

    Can be configured to be optional or required based on settings.

    Args:
        api_key: API key from header

    Returns:
        APIKeyInfo if authenticated

    Raises:
        HTTPException: If authentication is required but fails
    """
    settings = get_settings()

    # If authentication is disabled, allow all requests
    if not settings.require_api_key:
        return None

    if not api_key:
        logger.warning("api_key_missing", path="unknown")
        raise HTTPException(
            status_code=401,
            detail={"error_code": "AUTHENTICATION_ERROR", "message": "API key required"},
        )

    key_manager = get_key_manager()
    key_info = key_manager.validate_key(api_key)

    if not key_info:
        logger.warning("api_key_invalid", key_prefix=api_key[:10] if len(api_key) > 10 else "***")
        raise HTTPException(
            status_code=401,
            detail={"error_code": "AUTHENTICATION_ERROR", "message": "Invalid API key"},
        )

    logger.debug("api_key_validated", key_id=key_info.key_id)
    return key_info


# =============================================================================
# Rate Limiting
# =============================================================================


@dataclass
class RateLimitState:
    """State for a rate-limited client."""

    requests: list[float] = field(default_factory=list)
    blocked_until: Optional[float] = None


class RateLimiter:
    """In-memory rate limiter using sliding window.

    In production, use Redis for distributed rate limiting.
    """

    def __init__(
        self,
        requests_per_minute: int = RateLimitConfig.API_REQUESTS_PER_MINUTE,
        window_seconds: int = 60,
    ):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self._state: dict[str, RateLimitState] = defaultdict(RateLimitState)

    def _get_client_key(self, request: Request, api_key: Optional[APIKeyInfo]) -> str:
        """Get a unique key for the client."""
        if api_key:
            return f"key:{api_key.key_id}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        return f"ip:{client_ip}"

    def check_limit(
        self, request: Request, api_key: Optional[APIKeyInfo] = None
    ) -> tuple[bool, Optional[int]]:
        """Check if request is within rate limit.

        Args:
            request: The incoming request
            api_key: Optional API key info (may have custom rate limit)

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        client_key = self._get_client_key(request, api_key)
        state = self._state[client_key]
        now = time.time()

        # Check if client is blocked
        if state.blocked_until and now < state.blocked_until:
            retry_after = int(state.blocked_until - now)
            return False, retry_after

        # Clear old requests outside window
        cutoff = now - self.window_seconds
        state.requests = [t for t in state.requests if t > cutoff]

        # Get rate limit (custom or default)
        limit = (
            api_key.rate_limit
            if api_key and api_key.rate_limit
            else self.requests_per_minute
        )

        # Check if over limit
        if len(state.requests) >= limit:
            # Block for remainder of window
            state.blocked_until = now + self.window_seconds
            return False, self.window_seconds

        # Record request
        state.requests.append(now)
        return True, None

    def get_remaining(
        self, request: Request, api_key: Optional[APIKeyInfo] = None
    ) -> int:
        """Get remaining requests in current window."""
        client_key = self._get_client_key(request, api_key)
        state = self._state[client_key]
        now = time.time()

        # Clear old requests
        cutoff = now - self.window_seconds
        state.requests = [t for t in state.requests if t > cutoff]

        limit = (
            api_key.rate_limit
            if api_key and api_key.rate_limit
            else self.requests_per_minute
        )

        return max(0, limit - len(state.requests))


# Global rate limiter
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting."""

    def __init__(self, app, limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.limiter = limiter or get_rate_limiter()

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting for health check
        if request.url.path in ["/health", "/healthz", "/ready"]:
            return await call_next(request)

        settings = get_settings()
        if not settings.enable_rate_limiting:
            return await call_next(request)

        # Get API key if present
        api_key_header = request.headers.get("X-API-Key")
        api_key_info = None
        if api_key_header:
            key_manager = get_key_manager()
            api_key_info = key_manager.validate_key(api_key_header)

        is_allowed, retry_after = self.limiter.check_limit(request, api_key_info)

        if not is_allowed:
            logger.warning(
                "rate_limit_exceeded",
                path=request.url.path,
                retry_after=retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)

        # Add rate limit headers
        remaining = self.limiter.get_remaining(request, api_key_info)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(
            api_key_info.rate_limit
            if api_key_info and api_key_info.rate_limit
            else RateLimitConfig.API_REQUESTS_PER_MINUTE
        )

        return response


# =============================================================================
# Input Validation Utilities
# =============================================================================


def validate_reference(reference: str) -> str:
    """Validate and sanitize an application reference.

    Args:
        reference: The reference to validate

    Returns:
        Sanitized reference

    Raises:
        HTTPException: If reference is invalid
    """
    import re

    # Remove leading/trailing whitespace
    reference = reference.strip()

    # Check length
    if len(reference) < 5 or len(reference) > 50:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid reference format",
                "field": "reference",
            },
        )

    # Newcastle format: YYYY/NNNN/NN/XXX
    pattern = r"^\d{4}/\d{4}/\d{2}/[A-Z]{2,4}$"
    if not re.match(pattern, reference.upper()):
        # Be lenient but log
        logger.debug("non_standard_reference", reference=reference)

    # Sanitize: only allow alphanumeric, slashes, and hyphens
    sanitized = re.sub(r"[^A-Za-z0-9/\-]", "", reference)

    if sanitized != reference:
        logger.warning("reference_sanitized", original=reference, sanitized=sanitized)

    return sanitized.upper()


def validate_council_id(council_id: str) -> str:
    """Validate a council ID.

    Args:
        council_id: The council ID to validate

    Returns:
        Validated council ID

    Raises:
        HTTPException: If council ID is invalid
    """
    from plana.core.constants import SUPPORTED_COUNCILS

    council_id = council_id.lower().strip()

    if council_id not in SUPPORTED_COUNCILS:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": f"Unsupported council. Supported: {', '.join(SUPPORTED_COUNCILS)}",
                "field": "council_id",
            },
        )

    return council_id


def validate_pagination(page: int, page_size: int) -> tuple[int, int]:
    """Validate pagination parameters.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Tuple of (offset, limit) for database queries
    """
    from plana.core.constants import APIConfig

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = APIConfig.DEFAULT_PAGE_SIZE
    if page_size > APIConfig.MAX_PAGE_SIZE:
        page_size = APIConfig.MAX_PAGE_SIZE

    offset = (page - 1) * page_size
    return offset, page_size
