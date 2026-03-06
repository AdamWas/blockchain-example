"""
Certificate API – issuance and retrieval.
"""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.certificate import CertificateDetail, CertificateResponse
from app.services import certificate_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.post("", response_model=CertificateResponse, status_code=201)
async def issue_certificate(
    student_name: str = Form(...),
    course_name: str = Form(...),
    issuer_name: str = Form(...),
    issue_date: str = Form(...),
    file: UploadFile = File(..., description="The certificate PDF file"),
    student_email: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """
    Issue a new certificate.

    Accepts ``multipart/form-data`` with the student details and a PDF file.
    The file is hashed (SHA-256), uploaded to IPFS, recorded on the
    blockchain, and stored in the database.

    Returns **409** if a certificate for the same document already exists.
    """
    logger.info("Certificate issuance requested for student=%s course=%s", student_name, course_name)
    cert = await certificate_service.issue_certificate(
        student_name=student_name,
        course_name=course_name,
        issuer_name=issuer_name,
        issue_date=issue_date,
        file=file,
        db=db,
        student_email=student_email,
    )
    return cert


@router.get("/{certificate_id}", response_model=CertificateDetail)
def get_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """Retrieve full certificate metadata by its public UUID."""
    cert = certificate_service.get_certificate_by_id(certificate_id, db)
    if cert is None:
        raise HTTPException(status_code=404, detail="Certificate not found.")
    return cert
