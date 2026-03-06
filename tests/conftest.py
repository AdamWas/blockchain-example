"""
Shared test fixtures.

Every test gets its own temporary SQLite database and blockchain JSON
file so tests are fully isolated and can run in any order.  Mining
difficulty is set to 1 so proof-of-work completes instantly.
"""

import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# Keep difficulty low so mining is instant in tests
# ---------------------------------------------------------------------------
os.environ.setdefault("MINING_DIFFICULTY", "1")


@pytest.fixture(autouse=True)
def _isolated_env(tmp_path: Path, monkeypatch):
    """
    Redirect the database and blockchain to temporary files, and reset
    the blockchain singleton so each test starts from a clean genesis.
    """
    db_path = tmp_path / "test.db"
    chain_path = tmp_path / "test_chain.json"

    test_db_url = f"sqlite:///{db_path}"
    test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    Base.metadata.create_all(bind=test_engine)

    def _override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db

    monkeypatch.setattr("app.config.BLOCKCHAIN_FILE", str(chain_path))
    monkeypatch.setattr("app.blockchain.blockchain.BLOCKCHAIN_FILE", str(chain_path))
    monkeypatch.setattr("app.blockchain.blockchain.MINING_DIFFICULTY", 1)

    import app.services.blockchain_service as bc_svc
    bc_svc._blockchain = None

    yield

    app.dependency_overrides.clear()
    bc_svc._blockchain = None


@pytest.fixture()
def client():
    """httpx AsyncClient wired to the FastAPI app (no network needed)."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


SAMPLE_FORM = {
    "student_name": "Ada Lovelace",
    "student_email": "ada@example.com",
    "course_name": "Distributed Systems",
    "issuer_name": "Oxford University",
    "issue_date": "2026-03-06",
}

SAMPLE_PDF = b"%PDF-1.4 fake certificate content for testing"
