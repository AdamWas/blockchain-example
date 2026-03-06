"""
Verification API – verify certificates by file upload or by UUID.
"""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.verification import VerificationResponse, VerifyByIdRequest
from app.services import verification_service

router = APIRouter(prefix="/certificates/verify", tags=["Verification"])


@router.post("/file", response_model=VerificationResponse)
async def verify_by_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a file and verify whether a matching certificate exists
    on the blockchain.
    """
    file_bytes = await file.read()
    return verification_service.verify_by_file(file_bytes, db)


@router.post("/id", response_model=VerificationResponse)
def verify_by_id(
    body: VerifyByIdRequest,
    db: Session = Depends(get_db),
):
    """Verify a certificate by its UUID."""
    return verification_service.verify_by_id(body.certificate_id, db)
