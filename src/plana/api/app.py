"""
FastAPI application setup.
"""

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from plana.api.routes import applications, documents, feedback, health, jurisdiction, policies, reports, system
from plana.config import get_settings
from plana.documents.background import start_background_worker, stop_background_worker

logger = structlog.get_logger(__name__)


class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str
    path: str | None = None
    request_id: str | None = None
    error: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting Plana.AI API")
    settings = get_settings()
    settings.ensure_directories()

    # Log all registered routes at startup
    logger.info("=== REGISTERED ROUTES ===")
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            methods = ", ".join(sorted(route.methods - {"HEAD", "OPTIONS"})) if route.methods else "N/A"
            logger.info(f"  {methods:20} {route.path}")
    logger.info("=== END ROUTES ===")

    # Start the in-process document extraction worker
    start_background_worker()

    yield

    # Gracefully stop the background worker
    await stop_background_worker()
    logger.info("Shutting down Plana.AI API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Plana.AI API",
        description="AI-powered planning intelligence platform for UK planning applications",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Global exception handler for unhandled exceptions
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all unhandled exceptions and return JSON."""
        request_id = str(uuid.uuid4())[:8]

        # Log the full exception
        logger.exception(
            "Unhandled exception",
            request_id=request_id,
            path=str(request.url.path),
            method=request.method,
            error_type=type(exc).__name__,
        )

        # Determine if we should include error details
        debug = getattr(settings, "debug", False)

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal Server Error",
                "path": str(request.url.path),
                "request_id": request_id,
                "error": repr(exc) if debug else None,
            },
        )

    # Handle validation errors with JSON response
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle validation errors."""
        request_id = str(uuid.uuid4())[:8]

        logger.warning(
            "Validation error",
            request_id=request_id,
            path=str(request.url.path),
            errors=exc.errors(),
        )

        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation Error",
                "path": str(request.url.path),
                "request_id": request_id,
                "error": str(exc.errors()),
            },
        )

    # CORS middleware - allow all origins for public API (no credentials/cookies)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=86400,  # Cache preflight for 24 hours
    )

    # Register routers
    api_prefix = settings.api_prefix

    app.include_router(health.router, tags=["Health"])
    app.include_router(
        applications.router,
        prefix=f"{api_prefix}/applications",
        tags=["Applications"],
    )
    app.include_router(
        documents.router,
        prefix=f"{api_prefix}/documents",
        tags=["Documents"],
    )
    app.include_router(
        policies.router,
        prefix=f"{api_prefix}/policies",
        tags=["Policies"],
    )
    app.include_router(
        reports.router,
        prefix=f"{api_prefix}/reports",
        tags=["Reports"],
    )
    app.include_router(
        feedback.router,
        prefix=f"{api_prefix}/feedback",
        tags=["Feedback"],
    )
    app.include_router(
        jurisdiction.router,
        prefix=f"{api_prefix}/jurisdiction",
        tags=["Jurisdiction"],
    )
    app.include_router(
        system.router,
        prefix=f"{api_prefix}/system",
        tags=["System"],
    )

    return app
