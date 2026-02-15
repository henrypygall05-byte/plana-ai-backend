"""
Custom exceptions for Plana.AI.

Provides structured exception handling with proper error codes
and sanitized messages for API responses.
"""

from typing import Any, Optional


class PlanaError(Exception):
    """Base exception for all Plana errors."""

    error_code: str = "PLANA_ERROR"
    status_code: int = 500
    safe_message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """Initialize the exception.

        Args:
            message: Internal error message (may contain sensitive info)
            error_code: Override the default error code
            status_code: Override the default HTTP status code
            details: Additional details for logging (not exposed to clients)
        """
        super().__init__(message)
        if error_code:
            self.error_code = error_code
        if status_code:
            self.status_code = status_code
        self.details = details or {}
        self._internal_message = message

    @property
    def internal_message(self) -> str:
        """Get the internal message for logging."""
        return self._internal_message

    def to_api_response(self) -> dict[str, Any]:
        """Convert to a safe API response.

        Returns:
            Dictionary safe to return to clients
        """
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.safe_message,
        }


# =============================================================================
# Validation Errors (4xx)
# =============================================================================


class ValidationError(PlanaError):
    """Input validation failed."""

    error_code = "VALIDATION_ERROR"
    status_code = 400
    safe_message = "Invalid input provided"

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.field = field
        if field:
            self.safe_message = f"Invalid value for field: {field}"


class ReferenceNotFoundError(PlanaError):
    """Application reference not found."""

    error_code = "REFERENCE_NOT_FOUND"
    status_code = 404
    safe_message = "Application reference not found"

    def __init__(self, reference: str, **kwargs):
        super().__init__(f"Reference not found: {reference}", **kwargs)
        self.reference = reference
        self.safe_message = f"Application {reference} not found"


class CouncilMismatchError(PlanaError):
    """Supplied council_id conflicts with the application's stored council.

    Raised when a caller attempts to generate a report using a different
    council context than the one recorded on the application.  This is a
    hard guard — the system will NOT silently fall back to another
    council's policies or configuration.
    """

    error_code = "COUNCIL_MISMATCH"
    status_code = 409
    safe_message = "Council ID mismatch"

    def __init__(
        self,
        reference: str,
        expected: str,
        got: str,
        **kwargs,
    ):
        super().__init__(
            f"Council mismatch for {reference}: stored council is "
            f"'{expected}' but request supplied '{got}'",
            **kwargs,
        )
        self.reference = reference
        self.expected = expected
        self.got = got
        self.safe_message = (
            f"Council mismatch for {reference}: application belongs to "
            f"'{expected}', cannot process as '{got}'"
        )


class AuthenticationError(PlanaError):
    """Authentication failed."""

    error_code = "AUTHENTICATION_ERROR"
    status_code = 401
    safe_message = "Authentication required"


class AuthorizationError(PlanaError):
    """Authorization failed."""

    error_code = "AUTHORIZATION_ERROR"
    status_code = 403
    safe_message = "Access denied"


class RateLimitError(PlanaError):
    """Rate limit exceeded."""

    error_code = "RATE_LIMIT_EXCEEDED"
    status_code = 429
    safe_message = "Too many requests. Please try again later."

    def __init__(self, retry_after: Optional[int] = None, **kwargs):
        super().__init__("Rate limit exceeded", **kwargs)
        self.retry_after = retry_after


# =============================================================================
# Portal/External Errors
# =============================================================================


class PortalError(PlanaError):
    """Error accessing council portal."""

    error_code = "PORTAL_ERROR"
    status_code = 502
    safe_message = "Unable to access council portal"

    def __init__(
        self,
        message: str,
        *,
        url: Optional[str] = None,
        portal_status_code: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.url = url
        self.portal_status_code = portal_status_code


class PortalBlockedError(PortalError):
    """Portal has blocked automated access."""

    error_code = "PORTAL_BLOCKED"
    safe_message = "Council portal has blocked automated access"


class PortalUnavailableError(PortalError):
    """Portal is temporarily unavailable."""

    error_code = "PORTAL_UNAVAILABLE"
    status_code = 503
    safe_message = "Council portal is temporarily unavailable"


# =============================================================================
# Processing Errors
# =============================================================================


class ProcessingError(PlanaError):
    """Error during application processing."""

    error_code = "PROCESSING_ERROR"
    status_code = 500
    safe_message = "Error processing application"


class DocumentDownloadError(ProcessingError):
    """Error downloading document."""

    error_code = "DOCUMENT_DOWNLOAD_ERROR"
    safe_message = "Error downloading document"


class ReportGenerationError(ProcessingError):
    """Error generating report."""

    error_code = "REPORT_GENERATION_ERROR"
    safe_message = "Error generating report"


class PolicyRetrievalError(ProcessingError):
    """Error retrieving policies."""

    error_code = "POLICY_RETRIEVAL_ERROR"
    safe_message = "Error retrieving relevant policies"


# =============================================================================
# Database Errors
# =============================================================================


class DatabaseError(PlanaError):
    """Database operation failed."""

    error_code = "DATABASE_ERROR"
    status_code = 500
    safe_message = "Database operation failed"


class ConnectionError(DatabaseError):
    """Database connection failed."""

    error_code = "DATABASE_CONNECTION_ERROR"
    safe_message = "Unable to connect to database"


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(PlanaError):
    """Configuration error."""

    error_code = "CONFIGURATION_ERROR"
    status_code = 500
    safe_message = "Server configuration error"


class MissingConfigError(ConfigurationError):
    """Required configuration is missing."""

    error_code = "MISSING_CONFIG"

    def __init__(self, config_key: str, **kwargs):
        super().__init__(f"Missing required configuration: {config_key}", **kwargs)
        self.config_key = config_key
