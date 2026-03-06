"""
Pydantic schemas for blockchain-related responses.
"""

from typing import Any
from pydantic import BaseModel


class BlockSchema(BaseModel):
    index: int
    timestamp: str
    transactions: list[dict[str, Any]]
    previous_hash: str
    nonce: int
    hash: str


class BlockchainResponse(BaseModel):
    length: int
    chain: list[BlockSchema]


class BlockchainValidationResponse(BaseModel):
    valid: bool
    length: int
    message: str
