"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import Base, SessionLocal, engine
from .seed import run_all_seeds

# Import the configured Celery app so @shared_task instances bind to our
# Redis broker instead of Celery's default (amqp://localhost). Without this,
# generate_job.delay() in the web process tries to reach RabbitMQ and fails.
from . import celery_app as _celery_app  # noqa: F401

settings = get_settings()
logger = logging.getLogger("autocase")
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan: create tables + run idempotent seeds on startup."""
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)

    # Security warnings for default credentials
    if "change-me" in settings.secret_key.lower() or len(settings.secret_key) < 32:
        logger.warning("⚠ SECRET_KEY is too short or is the default placeholder. Generate a strong random key and set it via env!")
    if settings.initial_admin_password == "admin123":
        logger.warning("⚠ INITIAL_ADMIN_PASSWORD is the default 'admin123'. Change it before exposing this service!")

    # Import models so Base.metadata is populated
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Run first-run seeds (e.g. initial admin user)
    with SessionLocal() as db:
        run_all_seeds(db)

    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["meta"])
def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/api/version", tags=["meta"])
def version() -> dict:
    return {"version": settings.app_version}


# API v1 router
from .api.v1 import router as v1_router  # noqa: E402

app.include_router(v1_router, prefix=settings.api_prefix)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": exc.__class__.__name__},
    )
