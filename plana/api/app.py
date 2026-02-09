"""
FastAPI application for Plana.AI.

Provides REST API endpoints for Loveable frontend integration.
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from plana.api.errors import register_error_handlers
from plana.api.routes import applications, feedback, health, jurisdiction, reports
from plana.api.security import RateLimitMiddleware
from plana.config import get_settings
from plana.core.logging import configure_logging, get_logger, bind_context, clear_context

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    settings = get_settings()

    # Configure logging
    configure_logging(
        level=settings.log_level,
        json_output=settings.is_production,
    )

    # Validate production settings
    warnings = settings.validate_production_settings()
    for warning in warnings:
        logger.warning("config_warning", message=warning)

    logger.info(
        "application_startup",
        version=settings.app_version,
        environment=settings.environment,
        debug=settings.debug,
    )

    yield

    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app
    """
    settings = get_settings()

    app = FastAPI(
        title="Plana.AI API",
        description="Planning Intelligence Platform - REST API for Loveable integration",
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Configure CORS from settings
    cors_origins = settings.security.cors_origins
    allow_credentials = settings.security.cors_allow_credentials

    # In production, don't allow wildcard with credentials
    if "*" in cors_origins and allow_credentials:
        allow_credentials = False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*", "X-API-Key", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "X-RateLimit-Limit"],
        max_age=settings.security.cors_max_age,
    )

    # Add rate limiting middleware
    if settings.enable_rate_limiting:
        app.add_middleware(RateLimitMiddleware)

    # Add request ID middleware
    @app.middleware("http")
    async def add_request_context(request: Request, call_next):
        """Add request ID and timing to all requests."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id

        # Bind context for logging
        bind_context(request_id=request_id)

        # Track request timing
        start_time = time.time()

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            # Log request
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            return response
        finally:
            clear_context()

    # Register error handlers
    register_error_handlers(app)

    # Include routers - v1 API with prefix
    api_prefix = settings.api_prefix

    app.include_router(health.router, tags=["Health"])
    app.include_router(
        applications.router,
        prefix=f"{api_prefix}/applications",
        tags=["Applications"],
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

    # Also include at legacy paths for backward compatibility
    app.include_router(applications.router, prefix="/api/applications", tags=["Applications (Legacy)"])
    app.include_router(reports.router, prefix="/api/reports", tags=["Reports (Legacy)"])
    app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback (Legacy)"])
    app.include_router(jurisdiction.router, prefix="/api/jurisdiction", tags=["Jurisdiction (Legacy)"])

    return app


# Create app instance for uvicorn
app = create_app()
