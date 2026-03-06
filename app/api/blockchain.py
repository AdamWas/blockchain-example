"""
Blockchain API – inspect and validate the chain.
"""

from fastapi import APIRouter

from app.schemas.blockchain import BlockchainResponse, BlockchainValidationResponse
from app.services import blockchain_service

router = APIRouter(prefix="/blockchain", tags=["Blockchain"])


@router.get("", response_model=BlockchainResponse)
def get_blockchain():
    """Return the full blockchain."""
    chain = blockchain_service.get_chain_data()
    return BlockchainResponse(length=len(chain), chain=chain)


@router.get("/validate", response_model=BlockchainValidationResponse)
def validate_blockchain():
    """Validate the integrity of the entire blockchain."""
    valid, message = blockchain_service.validate()
    return BlockchainValidationResponse(
        valid=valid,
        length=blockchain_service.get_chain_length(),
        message=message,
    )
