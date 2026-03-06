"""
Pydantic schemas for certificate requests and responses.
"""

from datetime import datetime
from pydantic import BaseModel


class CertificateResponse(BaseModel):
    """Returned after a certificate is issued."""

    certificate_id: str
    student_name: str
    student_email: str | None = None
    course_name: str
    issuer_name: str
    issue_date: str
    document_hash: str
    ipfs_cid: str | None = None
    block_index: int
    transaction_id: str
    status: str

    model_config = {"from_attributes": True}


class CertificateDetail(CertificateResponse):
    """Full certificate record including the database timestamp."""

    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
