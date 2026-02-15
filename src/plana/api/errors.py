"""
Standardized error handling for Plana.AI API.

Provides consistent error response format and error handlers.
"""

import traceback
from typing import Any, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from plana.core.exceptions import PlanaError
from plana.core.logging import get_logger

logger = get_logger(__name__)


class APIErrorResponse:
    """Standardized API error response format."""

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.request_id = request_id

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        response = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
        }

        if self.details:
            response["details"] = self.details

        if self.request_id:
            response["request_id"] = self.request_id

        return response

    def to_response(self) -> JSONResponse:
        """Convert to FastAPI JSONResponse."""
        return JSONResponse(
            status_code=self.status_code,
            content=self.to_dict(),
        )


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 500,
    details: Optional[dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> JSONResponse:
    """Create a standardized error response.

    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        request: Optional request for context

    Returns:
        JSONResponse with standardized format
    """
    request_id = None
    if request:
        request_id = getattr(request.state, "request_id", None)

    return APIErrorResponse(
        error_code=error_code,
        message=message,
        status_code=status_code,
        details=details,
        request_id=request_id,
    ).to_response()


async def plana_exception_handler(
    request: Request, exc: PlanaError
) -> JSONResponse:
    """Handle PlanaError exceptions.

    Logs the internal message but returns the safe message to clients.
    """
    request_id = getattr(request.state, "request_id", None)

    logger.error(
        "plana_error",
        error_code=exc.error_code,
        internal_message=exc.internal_message,
        path=request.url.path,
        request_id=request_id,
        details=exc.details,
    )

    return create_error_response(
        error_code=exc.error_code,
        message=exc.safe_message,
        status_code=exc.status_code,
        request=request,
    )


async def http_exception_handler(
    request: Request, exc: Union[HTTPException, StarletteHTTPException]
) -> JSONResponse:
    """Handle FastAPI/Starlette HTTP exceptions."""
    request_id = getattr(request.state, "request_id", None)

    # Extract error details
    if isinstance(exc.detail, dict):
        error_code = exc.detail.get("error_code", "HTTP_ERROR")
        message = exc.detail.get("message", str(exc.detail))
        details = exc.detail.get("details")
    else:
        error_code = f"HTTP_{exc.status_code}"
        message = str(exc.detail) if exc.detail else "An error occurred"
        details = None

    logger.warning(
        "http_error",
        status_code=exc.status_code,
        error_code=error_code,
        message=message,
        path=request.url.path,
        request_id=request_id,
    )

    return create_error_response(
        error_code=error_code,
        message=message,
        status_code=exc.status_code,
        details=details,
        request=request,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    request_id = getattr(request.state, "request_id", None)

    # Format validation errors
    errors = []
    for error in exc.errors():
        loc = ".".join(str(x) for x in error["loc"])
        errors.append({
            "field": loc,
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(
        "validation_error",
        errors=errors,
        path=request.url.path,
        request_id=request_id,
    )

    return create_error_response(
        error_code="VALIDATION_ERROR",
        message="Invalid request data",
        status_code=422,
        details={"errors": errors},
        request=request,
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions.

    Logs the full traceback but returns a generic message to clients
    to avoid leaking internal details.
    """
    request_id = getattr(request.state, "request_id", None)

    # Log full traceback
    logger.error(
        "unhandled_exception",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        traceback=traceback.format_exc(),
        path=request.url.path,
        method=request.method,
        request_id=request_id,
    )

    # Return generic error to client (don't leak internal details)
    return create_error_response(
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        status_code=500,
        request=request,
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all error handlers with a FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Plana-specific exceptions
    app.add_exception_handler(PlanaError, plana_exception_handler)

    # HTTP exceptions (FastAPI and Starlette)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Catch-all for unexpected errors
    app.add_exception_handler(Exception, generic_exception_handler)
