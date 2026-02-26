from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.admin import wire_admin_router
from src.api.routers.catalog import wire_catalog_router
from src.api.routers.engagement import wire_engagement_router
from src.core.config import get_settings
from src.db.init_db import initialize_database
from src.db.session import create_engine_and_sessionmaker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("car_brochure_backend")

openapi_tags = [
    {"name": "Catalog", "description": "Public car browsing, search/filter, details, and comparison."},
    {"name": "Engagement", "description": "Favorites and inquiry submission."},
    {"name": "Admin", "description": "Admin management for categories, cars, images, and inquiries."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan: initialize DB and seed demo data on startup.

    Side effects:
      - Creates missing tables.
      - Seeds a small set of demo categories/cars if database is empty.

    Failure modes:
      1) Missing POSTGRES_* env vars -> ValueError at startup.
      2) DB unreachable/invalid URL -> SQLAlchemy error.
      3) Migration/schema issues -> SQL errors during create_all.
    """
    settings = get_settings()
    engine, session_maker = create_engine_and_sessionmaker(settings)

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_maker = session_maker

    logger.info("Startup: initializing database")
    await initialize_database(engine)
    logger.info("Startup: database initialized")

    yield

    logger.info("Shutdown: disposing DB engine")
    await engine.dispose()


app = FastAPI(
    title="Car Brochure API",
    description="Backend API for browsing and managing car listings, favorites, comparisons, and inquiries.",
    version="1.0.0",
    openapi_tags=openapi_tags,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # frontend deployed separately; tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    summary="Health check",
    description="Health endpoint to verify the service is up.",
    tags=["Catalog"],
    operation_id="health_check",
)
def health_check():
    """Health check endpoint.

    Returns:
      JSON with a simple status message.
    """
    return {"message": "Healthy"}


# Router wiring (single canonical wiring point)
def _include_routers() -> None:
    session_maker = app.state.session_maker
    settings = app.state.settings
    app.include_router(wire_catalog_router(session_maker=session_maker))
    app.include_router(wire_engagement_router(session_maker=session_maker))
    app.include_router(wire_admin_router(session_maker=session_maker, settings=settings))


@app.on_event("startup")
async def _startup_include_routers():
    # lifespan has already populated state by this point
    _include_routers()
