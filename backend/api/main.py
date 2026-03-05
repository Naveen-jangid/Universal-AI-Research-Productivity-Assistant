"""
FastAPI application entry point.
Registers all routers, middleware, and startup/shutdown hooks.
"""

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes import agent, audio, chat, data_analysis, documents, images
from backend.core.config import settings
from backend.core.database import init_db
from backend.core.logging_config import setup_logging

logger = logging.getLogger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown logic."""
    # Setup
    setup_logging()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)

    # Ensure required directories exist
    for d in ["uploads", "uploads/documents", "uploads/images", "uploads/audio",
              "uploads/data", "vectorstore", "memory", "logs"]:
        Path(d).mkdir(parents=True, exist_ok=True)

    # Initialise SQLite schema
    init_db()
    logger.info("Database initialised.")

    yield

    # Shutdown
    logger.info("Application shutting down.")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-ready Generative AI backend with RAG, vision, speech, "
            "autonomous agents, data analysis, and long-term memory."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── Middleware ─────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ── Request timing middleware ──────────────────────────────────────────
    @app.middleware("http")
    async def add_timing_header(request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.1f}"
        return response

    # ── Routers ────────────────────────────────────────────────────────────
    api_prefix = "/api/v1"
    app.include_router(chat.router, prefix=api_prefix)
    app.include_router(documents.router, prefix=api_prefix)
    app.include_router(images.router, prefix=api_prefix)
    app.include_router(audio.router, prefix=api_prefix)
    app.include_router(data_analysis.router, prefix=api_prefix)
    app.include_router(agent.router, prefix=api_prefix)

    # ── Health check ───────────────────────────────────────────────────────
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "openai_configured": bool(settings.OPENAI_API_KEY),
        }

    @app.get("/", tags=["System"])
    async def root():
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "docs": "/docs",
            "health": "/health",
        }

    # ── Global exception handler ───────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again later."},
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
