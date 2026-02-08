"""
FastAPI application for Plana.AI.

Provides REST API endpoints for Loveable frontend integration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from plana.api.routes import applications, feedback, health, jurisdiction, reports


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="Plana.AI API",
        description="Planning Intelligence Platform - REST API for Loveable integration",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware for Loveable frontend - allow all origins for public API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Must be False when using wildcard origins
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=86400,  # Cache preflight for 24 hours
    )

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
    app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
    app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
    app.include_router(jurisdiction.router, prefix="/api/jurisdiction", tags=["Jurisdiction"])

    return app


# Create app instance for uvicorn
app = create_app()
