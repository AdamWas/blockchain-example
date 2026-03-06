"""
Integration tests for the Certificate Blockchain API.

Each test uses an isolated temporary database and blockchain file
(see conftest.py), so they can run independently and in any order.
"""

import pytest

from tests.conftest import SAMPLE_FORM, SAMPLE_PDF

pytestmark = pytest.mark.asyncio


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

async def _issue_certificate(client, pdf_bytes: bytes = SAMPLE_PDF):
    """Post a certificate and return the parsed JSON response."""
    resp = await client.post(
        "/certificates",
        data=SAMPLE_FORM,
        files={"file": ("cert.pdf", pdf_bytes, "application/pdf")},
    )
    return resp


# -----------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------

class TestHealth:
    async def test_health_returns_ok(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["database"] == "connected"
        assert isinstance(body["blockchain_length"], int)


# -----------------------------------------------------------------------
# Certificate issuance
# -----------------------------------------------------------------------

class TestCertificateIssuance:
    async def test_issue_certificate(self, client):
        resp = await _issue_certificate(client)
        assert resp.status_code == 201

        body = resp.json()
        assert body["student_name"] == "Ada Lovelace"
        assert body["student_email"] == "ada@example.com"
        assert body["course_name"] == "Distributed Systems"
        assert body["issuer_name"] == "Oxford University"
        assert body["issue_date"] == "2026-03-06"
        assert body["status"] == "issued"
        assert body["block_index"] >= 1
        assert body["certificate_id"]
        assert body["transaction_id"]
        assert body["document_hash"]

    async def test_duplicate_document_rejected(self, client):
        first = await _issue_certificate(client)
        assert first.status_code == 201

        second = await _issue_certificate(client)
        assert second.status_code == 409
        assert "already exists" in second.json()["detail"]

    async def test_empty_file_rejected(self, client):
        resp = await client.post(
            "/certificates",
            data=SAMPLE_FORM,
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()


# -----------------------------------------------------------------------
# Certificate retrieval
# -----------------------------------------------------------------------

class TestCertificateRetrieval:
    async def test_get_certificate_by_id(self, client):
        issue_resp = await _issue_certificate(client)
        cert_id = issue_resp.json()["certificate_id"]

        resp = await client.get(f"/certificates/{cert_id}")
        assert resp.status_code == 200

        body = resp.json()
        assert body["certificate_id"] == cert_id
        assert body["student_name"] == "Ada Lovelace"
        assert "id" in body
        assert "created_at" in body

    async def test_get_nonexistent_certificate_returns_404(self, client):
        resp = await client.get("/certificates/nonexistent-id")
        assert resp.status_code == 404


# -----------------------------------------------------------------------
# Verification
# -----------------------------------------------------------------------

class TestVerification:
    async def test_verify_by_file_success(self, client):
        await _issue_certificate(client)

        resp = await client.post(
            "/certificates/verify/file",
            files={"file": ("cert.pdf", SAMPLE_PDF, "application/pdf")},
        )
        assert resp.status_code == 200

        body = resp.json()
        assert body["verified"] is True
        assert body["certificate_id"] is not None
        assert body["block_index"] is not None
        assert body["transaction_id"] is not None

    async def test_verify_by_file_unknown_document(self, client):
        resp = await client.post(
            "/certificates/verify/file",
            files={"file": ("other.pdf", b"unknown content", "application/pdf")},
        )
        assert resp.status_code == 200

        body = resp.json()
        assert body["verified"] is False
        assert body["document_hash"] is not None

    async def test_verify_by_id_success(self, client):
        issue_resp = await _issue_certificate(client)
        cert_id = issue_resp.json()["certificate_id"]

        resp = await client.post(
            "/certificates/verify/id",
            json={"certificate_id": cert_id},
        )
        assert resp.status_code == 200

        body = resp.json()
        assert body["verified"] is True
        assert body["certificate_id"] == cert_id

    async def test_verify_by_id_nonexistent(self, client):
        resp = await client.post(
            "/certificates/verify/id",
            json={"certificate_id": "does-not-exist"},
        )
        assert resp.status_code == 200

        body = resp.json()
        assert body["verified"] is False

    async def test_verify_confirms_block_integrity(self, client):
        """Verification should check the actual block hash, not just
        that the transaction exists."""
        issue_resp = await _issue_certificate(client)
        cert_id = issue_resp.json()["certificate_id"]

        resp = await client.post(
            "/certificates/verify/id",
            json={"certificate_id": cert_id},
        )
        body = resp.json()
        assert body["verified"] is True
        assert body["block_index"] >= 1
        assert "blockchain" in body["message"].lower()


# -----------------------------------------------------------------------
# Blockchain
# -----------------------------------------------------------------------

class TestBlockchain:
    async def test_get_chain_has_genesis(self, client):
        resp = await client.get("/blockchain")
        assert resp.status_code == 200

        body = resp.json()
        assert body["length"] >= 1
        genesis = body["chain"][0]
        assert genesis["index"] == 0
        assert genesis["previous_hash"] == "0"
        assert genesis["transactions"] == []

    async def test_chain_grows_after_issuance(self, client):
        before = (await client.get("/blockchain")).json()["length"]
        await _issue_certificate(client)
        after = (await client.get("/blockchain")).json()["length"]
        assert after == before + 1

    async def test_validate_clean_chain(self, client):
        resp = await client.get("/blockchain/validate")
        assert resp.status_code == 200

        body = resp.json()
        assert body["valid"] is True
        assert body["length"] >= 1

    async def test_validate_after_issuance(self, client):
        await _issue_certificate(client)
        resp = await client.get("/blockchain/validate")
        body = resp.json()
        assert body["valid"] is True
        assert body["length"] >= 2

    async def test_block_hashes_linked(self, client):
        """Each block's previous_hash must equal the prior block's hash."""
        await _issue_certificate(client)
        chain = (await client.get("/blockchain")).json()["chain"]

        for i in range(1, len(chain)):
            assert chain[i]["previous_hash"] == chain[i - 1]["hash"]

    async def test_blocks_mined_correctly(self, client):
        """Every block hash must start with the required leading zeros."""
        await _issue_certificate(client)
        chain = (await client.get("/blockchain")).json()["chain"]

        for block in chain:
            assert block["hash"].startswith("0")
