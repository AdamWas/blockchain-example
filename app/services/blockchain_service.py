"""
Blockchain service – provides the application-wide Blockchain instance
and exposes high-level operations used by other services.

The singleton is created lazily on first access so that importing this
module does not trigger file I/O or genesis-block creation as a side
effect.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from app.blockchain.blockchain import Blockchain

logger = logging.getLogger(__name__)

_blockchain: Blockchain | None = None


def get_blockchain() -> Blockchain:
    """Return (and lazily create) the application-wide Blockchain instance."""
    global _blockchain
    if _blockchain is None:
        _blockchain = Blockchain()
    return _blockchain


def add_certificate_transaction(payload: dict[str, Any], transaction_id: str) -> int:
    """
    Record a ``CERTIFICATE_ISSUED`` transaction and mine a new block.

    Returns the index of the newly created block.
    """
    transaction = {
        "transaction_id": transaction_id,
        "type": "CERTIFICATE_ISSUED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }

    chain = get_blockchain()
    block = chain.add_block([transaction])
    logger.info(
        "Recorded transaction %s in block %d",
        transaction_id, block.index,
    )
    return block.index


def validate() -> tuple[bool, str]:
    """Validate the entire blockchain and return ``(valid, message)``."""
    return get_blockchain().validate_chain()


def find_transaction(transaction_id: str) -> dict[str, Any] | None:
    """Look up a transaction by its id across all blocks."""
    return get_blockchain().find_transaction(transaction_id)


def get_chain_data() -> list[dict[str, Any]]:
    """Return the full chain as serialisable dicts."""
    return get_blockchain().to_dict_list()


def get_chain_length() -> int:
    """Return the number of blocks in the chain."""
    return len(get_blockchain().chain)
