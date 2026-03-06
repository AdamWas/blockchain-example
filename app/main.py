"""
FastAPI application entry point.

- Configures structured logging.
- Creates database tables on startup.
- Registers all routers.
- Installs a global exception handler so unhandled errors never leak
  raw stack traces to API consumers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.api import blockchain, certificates, health, verification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create database tables when the application starts."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified")
    yield


app = FastAPI(
    title="Blockchain Certificate System",
    description=(
        "REST API for issuing and verifying educational certificates "
        "backed by a custom blockchain and IPFS."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    """
    Catch-all handler that prevents unhandled exceptions from leaking
    internal details to the client.
    """
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


app.include_router(health.router)
app.include_router(certificates.router)
app.include_router(verification.router)
app.include_router(blockchain.router)
