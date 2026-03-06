"""
Pydantic schemas for verification endpoints.
"""

from pydantic import BaseModel


class VerifyByIdRequest(BaseModel):
    """Body for verifying a certificate by its UUID."""

    certificate_id: str


class VerificationResponse(BaseModel):
    """Unified response returned by all verification endpoints."""

    verified: bool
    message: str
    certificate_id: str | None = None
    document_hash: str | None = None
    block_index: int | None = None
    transaction_id: str | None = None
