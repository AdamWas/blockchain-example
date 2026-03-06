"""
Certificate service – orchestrates the full issuance pipeline: file
hashing, IPFS upload, blockchain recording, and database persistence.
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.certificate import Certificate
from app.services import blockchain_service, ipfs_service
from app.utils.hashing import sha256_hash

logger = logging.getLogger(__name__)


async def issue_certificate(
    student_name: str,
    course_name: str,
    issuer_name: str,
    issue_date: str,
    file: UploadFile,
    db: Session,
    student_email: str | None = None,
) -> Certificate:
    """
    Full issuance pipeline:

    1. Read the uploaded file and validate it is non-empty.
    2. Compute the SHA-256 hash and check for duplicates.
    3. Upload the file to IPFS.
    4. Build a blockchain transaction and mine a new block.
    5. Persist the certificate metadata in SQLite.

    Raises :class:`HTTPException` (409) if a certificate with the same
    document hash already exists.
    """
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    document_hash = sha256_hash(file_bytes)

    existing = get_certificate_by_hash(document_hash, db)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A certificate for this document already exists "
                f"(certificate_id={existing.certificate_id})."
            ),
        )

    ipfs_cid = ipfs_service.upload_to_ipfs(file_bytes, file.filename or "document")

    certificate_id = str(uuid.uuid4())
    transaction_id = str(uuid.uuid4())

    payload = {
        "certificate_id": certificate_id,
        "student_name": student_name,
        "course_name": course_name,
        "issuer_name": issuer_name,
        "issue_date": issue_date,
        "document_hash": document_hash,
        "ipfs_cid": ipfs_cid,
    }

    block_index = blockchain_service.add_certificate_transaction(payload, transaction_id)

    cert = Certificate(
        certificate_id=certificate_id,
        student_name=student_name,
        student_email=student_email,
        course_name=course_name,
        issuer_name=issuer_name,
        issue_date=issue_date,
        document_hash=document_hash,
        ipfs_cid=ipfs_cid,
        block_index=block_index,
        transaction_id=transaction_id,
        status="issued",
        created_at=datetime.now(timezone.utc),
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)

    logger.info(
        "Issued certificate %s for %s (block %d)",
        certificate_id, student_name, block_index,
    )
    return cert


def get_certificate_by_id(certificate_id: str, db: Session) -> Certificate | None:
    """Fetch a certificate by its public UUID."""
    return (
        db.query(Certificate)
        .filter(Certificate.certificate_id == certificate_id)
        .first()
    )


def get_certificate_by_hash(document_hash: str, db: Session) -> Certificate | None:
    """Fetch a certificate by the SHA-256 hash of its document."""
    return (
        db.query(Certificate)
        .filter(Certificate.document_hash == document_hash)
        .first()
    )
