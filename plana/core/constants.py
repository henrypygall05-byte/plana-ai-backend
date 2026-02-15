"""
Constants and magic numbers for Plana.AI.

This module centralizes all magic numbers and configuration constants
to improve maintainability and make values easily adjustable.
"""

from typing import Final


# =============================================================================
# Similarity Search Thresholds
# =============================================================================

class SimilarityThresholds:
    """Threshold values for similarity scoring."""

    # Minimum score for a case to be considered similar
    MINIMUM_SIMILARITY: Final[float] = 0.2

    # Score at which a case is considered moderately similar
    MODERATE_SIMILARITY: Final[float] = 0.5

    # Score at which a case is considered highly similar
    HIGH_SIMILARITY: Final[float] = 0.6

    # Maximum similarity score
    MAXIMUM_SIMILARITY: Final[float] = 1.0

    # Default number of similar cases to return
    DEFAULT_MAX_RESULTS: Final[int] = 10


# =============================================================================
# Policy Search Configuration
# =============================================================================

class PolicySearchConfig:
    """Configuration for policy search and ranking."""

    # Maximum number of policies to return
    DEFAULT_MAX_RESULTS: Final[int] = 15

    # Boost applied when keyword matches
    KEYWORD_MATCH_BOOST: Final[float] = 0.3

    # Minimum term length for tokenization
    MIN_TERM_LENGTH: Final[int] = 3


# =============================================================================
# Confidence Adjustment
# =============================================================================

class ConfidenceConfig:
    """Configuration for confidence scoring."""

    # Base confidence for predictions
    BASE_CONFIDENCE: Final[float] = 0.75

    # Maximum confidence allowed
    MAX_CONFIDENCE: Final[float] = 0.95

    # Minimum confidence floor
    MIN_CONFIDENCE: Final[float] = 0.5

    # Adjustment step for feedback-based changes
    FEEDBACK_ADJUSTMENT_STEP: Final[float] = 0.05


# =============================================================================
# Rate Limiting
# =============================================================================

class RateLimitConfig:
    """Rate limiting configuration."""

    # API rate limit (requests per minute)
    API_REQUESTS_PER_MINUTE: Final[int] = 60

    # Portal request interval (seconds between requests)
    PORTAL_REQUEST_INTERVAL: Final[float] = 1.0

    # Maximum retries for portal requests
    PORTAL_MAX_RETRIES: Final[int] = 3

    # Retry backoff multiplier
    RETRY_BACKOFF_MULTIPLIER: Final[float] = 2.0


# =============================================================================
# Document Processing
# =============================================================================

class DocumentConfig:
    """Document processing configuration."""

    # Maximum concurrent downloads
    MAX_CONCURRENT_DOWNLOADS: Final[int] = 5

    # Download chunk size in bytes
    DOWNLOAD_CHUNK_SIZE: Final[int] = 8192

    # Maximum document title length for filenames
    MAX_TITLE_LENGTH: Final[int] = 50

    # Default timeout for downloads (seconds)
    DOWNLOAD_TIMEOUT: Final[int] = 30


# =============================================================================
# Database Configuration
# =============================================================================

class DatabaseConfig:
    """Database configuration constants."""

    # Default connection pool size
    DEFAULT_POOL_SIZE: Final[int] = 10

    # Maximum overflow connections
    MAX_OVERFLOW: Final[int] = 20

    # Connection timeout (seconds)
    CONNECT_TIMEOUT: Final[int] = 10

    # Query timeout (seconds)
    QUERY_TIMEOUT: Final[int] = 30


# =============================================================================
# Cache Configuration
# =============================================================================

class CacheConfig:
    """Cache configuration constants."""

    # Default cache TTL (seconds)
    DEFAULT_TTL: Final[int] = 3600

    # Policy cache TTL (seconds) - policies change infrequently
    POLICY_CACHE_TTL: Final[int] = 86400  # 24 hours

    # Maximum cache size (number of entries)
    MAX_CACHE_SIZE: Final[int] = 1000


# =============================================================================
# API Configuration
# =============================================================================

class APIConfig:
    """API configuration constants."""

    # Default page size for paginated endpoints
    DEFAULT_PAGE_SIZE: Final[int] = 50

    # Maximum page size
    MAX_PAGE_SIZE: Final[int] = 100

    # Request timeout (seconds)
    REQUEST_TIMEOUT: Final[int] = 30

    # Maximum request body size (bytes)
    MAX_BODY_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB


# =============================================================================
# QC/Benchmark Configuration
# =============================================================================

class QCConfig:
    """Quality control configuration."""

    # Passing QC threshold (percentage)
    PASSING_THRESHOLD: Final[float] = 70.0

    # Partial match weight
    PARTIAL_MATCH_WEIGHT: Final[float] = 0.5

    # Full match weight
    FULL_MATCH_WEIGHT: Final[float] = 1.0


# =============================================================================
# Supported Councils
# =============================================================================

SUPPORTED_COUNCILS: Final[list[str]] = ["newcastle", "broxtowe"]

# Council display names
COUNCIL_NAMES: Final[dict[str, str]] = {
    "newcastle": "Newcastle City Council",
    "broxtowe": "Broxtowe Borough Council",
    "gateshead": "Gateshead Council",
    "north_tyneside": "North Tyneside Council",
    "nottingham": "Nottingham City Council",
    "erewash": "Erewash Borough Council",
}


UNKNOWN_COUNCIL_NAME: Final[str] = "Unknown Council"


def resolve_council_name(council_id: str) -> str:
    """Resolve a council_id to its display name.

    Args:
        council_id: Council identifier (e.g. 'broxtowe').
                    Empty or None returns ``UNKNOWN_COUNCIL_NAME`` with a
                    warning so the caller can decide how to handle it.

    Returns:
        Full council name (e.g. 'Broxtowe Borough Council').
        Falls back to title-cased council_id if not in the lookup table.
        Returns "Unknown Council" (with a warning) when *council_id* is
        empty/None — report generation must never silently assume
        "Newcastle".
    """
    if not council_id or not council_id.strip():
        import warnings
        warnings.warn(
            "council_id is empty — returning 'Unknown Council'. "
            "Ensure the frontend sends council_id on import.",
            stacklevel=2,
        )
        return UNKNOWN_COUNCIL_NAME
    return COUNCIL_NAMES.get(council_id.lower(), council_id.replace("_", " ").title())
