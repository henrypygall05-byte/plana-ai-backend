"""
Structured logging configuration for Plana.AI.

Uses structlog for structured, context-aware logging with
support for both development (console) and production (JSON) formats.
"""

import logging
import sys
from typing import Any, Optional

import structlog
from structlog.types import Processor


def configure_logging(
    level: str = "INFO",
    json_output: bool = False,
    add_timestamp: bool = True,
) -> None:
    """Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, output JSON format; otherwise pretty console output
        add_timestamp: If True, add timestamps to log entries
    """
    # Configure stdlib logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Build processor chain
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso") if add_timestamp else _identity,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        # Production: JSON output
        processors: list[Processor] = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Pretty console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _identity(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Identity processor that does nothing (used to skip timestamp)."""
    return event_dict


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (usually __name__ of the calling module)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Convenience function for adding context
def bind_context(**kwargs: Any) -> None:
    """Bind context variables to all subsequent log messages.

    Example:
        bind_context(request_id="abc123", user_id="user456")
        logger.info("Processing request")  # Will include request_id and user_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()


def unbind_context(*keys: str) -> None:
    """Unbind specific context variables.

    Args:
        keys: Keys to unbind
    """
    structlog.contextvars.unbind_contextvars(*keys)


# =============================================================================
# Specialized Loggers
# =============================================================================


class RequestLogger:
    """Logger for HTTP request/response logging."""

    def __init__(self):
        self._logger = get_logger("plana.api.requests")

    def log_request(
        self,
        method: str,
        path: str,
        *,
        request_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log an incoming request."""
        self._logger.info(
            "request_received",
            method=method,
            path=path,
            request_id=request_id,
            client_ip=client_ip,
            user_agent=user_agent,
        )

    def log_response(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        *,
        request_id: Optional[str] = None,
    ) -> None:
        """Log a response."""
        log_method = self._logger.info if status_code < 400 else self._logger.warning
        log_method(
            "request_completed",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            request_id=request_id,
        )


class PipelineLogger:
    """Logger for pipeline processing."""

    def __init__(self, reference: str, mode: str = "demo"):
        self._logger = get_logger("plana.pipeline")
        self.reference = reference
        self.mode = mode

    def step_started(self, step_name: str, **kwargs: Any) -> None:
        """Log step start."""
        self._logger.info(
            "pipeline_step_started",
            reference=self.reference,
            mode=self.mode,
            step=step_name,
            **kwargs,
        )

    def step_completed(
        self, step_name: str, duration_ms: float, **kwargs: Any
    ) -> None:
        """Log step completion."""
        self._logger.info(
            "pipeline_step_completed",
            reference=self.reference,
            mode=self.mode,
            step=step_name,
            duration_ms=round(duration_ms, 2),
            **kwargs,
        )

    def step_failed(
        self, step_name: str, error: str, **kwargs: Any
    ) -> None:
        """Log step failure."""
        self._logger.error(
            "pipeline_step_failed",
            reference=self.reference,
            mode=self.mode,
            step=step_name,
            error=error,
            **kwargs,
        )

    def pipeline_completed(
        self, success: bool, duration_ms: float, **kwargs: Any
    ) -> None:
        """Log pipeline completion."""
        log_method = self._logger.info if success else self._logger.error
        log_method(
            "pipeline_completed",
            reference=self.reference,
            mode=self.mode,
            success=success,
            duration_ms=round(duration_ms, 2),
            **kwargs,
        )


class PortalLogger:
    """Logger for portal interactions."""

    def __init__(self, council_id: str):
        self._logger = get_logger("plana.portal")
        self.council_id = council_id

    def request_started(self, url: str, method: str = "GET") -> None:
        """Log portal request start."""
        self._logger.debug(
            "portal_request_started",
            council_id=self.council_id,
            url=url,
            method=method,
        )

    def request_completed(
        self, url: str, status_code: int, duration_ms: float
    ) -> None:
        """Log portal request completion."""
        log_method = self._logger.debug if status_code < 400 else self._logger.warning
        log_method(
            "portal_request_completed",
            council_id=self.council_id,
            url=url,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
        )

    def request_failed(self, url: str, error: str, attempt: int = 1) -> None:
        """Log portal request failure."""
        self._logger.warning(
            "portal_request_failed",
            council_id=self.council_id,
            url=url,
            error=error,
            attempt=attempt,
        )

    def blocked(self, url: str, reason: str) -> None:
        """Log portal access blocked."""
        self._logger.error(
            "portal_access_blocked",
            council_id=self.council_id,
            url=url,
            reason=reason,
        )
