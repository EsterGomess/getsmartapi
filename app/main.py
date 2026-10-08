"""
Main entry point for the FastAPI application.
This module initializes the FastAPI app, configures settings, and includes API routers.
"""

from fastapi import FastAPI
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import setup_logging
from app.middleware.logging import log_requests
from app.api.routers.v1 import (
    auth_router, customer_auth_router,
    note_router, topic_router)

IS_PRODUCTION = settings.ENV.lower() == "production"
DOCS_URL = "/docs" if settings.SHOW_DOCS else None
REDOC_URL = "/redoc" if settings.SHOW_DOCS else None
OPENAPI_URL = "/openapi.json" if settings.SHOW_DOCS else None

setup_logging(json_logs=IS_PRODUCTION)

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    docs_url=DOCS_URL,
    redoc_url=REDOC_URL,
    openapi_url=OPENAPI_URL,
)

app.middleware("http")(log_requests)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/health")
async def health():
    """Check the health of the application."""
    return {"status": "ok"}
app.include_router(auth_router,prefix="/api/v1",)
app.include_router(customer_auth_router,prefix="/api/v1",)
app.include_router(note_router,prefix="/api/v1",)
app.include_router(topic_router,prefix="/api/v1",)