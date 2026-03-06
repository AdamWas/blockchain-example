"""
Health-check endpoint.

Returns basic diagnostic information: service status, blockchain length,
and database connectivity.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import blockchain_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Liveness / readiness probe.

    Reports the service status, number of blocks in the chain,
    and whether the database is reachable.
    """
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "blockchain_length": blockchain_service.get_chain_length(),
    }
