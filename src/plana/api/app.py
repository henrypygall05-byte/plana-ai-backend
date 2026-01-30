"""
FastAPI application setup.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from plana.api.routes import applications, documents, feedback, health, policies, reports
from plana.config import get_settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting Plana.AI API")
    settings = get_settings()
    settings.ensure_directories()
    yield
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

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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

    return app
