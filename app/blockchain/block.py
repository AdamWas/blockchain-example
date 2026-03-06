"""
Block definition for the custom blockchain.

A block is the fundamental unit of the chain.  It holds:

- **index**: position in the chain (0 for genesis).
- **timestamp**: ISO-8601 creation time (UTC).
- **transactions**: ordered list of transaction dicts.
- **previous_hash**: SHA-256 hash of the preceding block (``"0"`` for genesis).
- **nonce**: counter incremented during proof-of-work mining.
- **hash**: SHA-256 digest of all the above fields – this is what makes
  the block immutable once mined.

The hash is computed deterministically from the block's content via
:py:meth:`compute_hash`, which serialises the fields to a canonical JSON
string (``sort_keys=True``) before hashing.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


class Block:
    """Single block in the blockchain."""

    def __init__(
        self,
        index: int,
        transactions: list[dict[str, Any]],
        previous_hash: str,
        nonce: int = 0,
        timestamp: str | None = None,
        block_hash: str | None = None,
    ):
        self.index = index
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        # When loading from disk we trust the stored hash; for new blocks we
        # compute it from the contents so the caller can then mine it.
        self.hash = block_hash or self.compute_hash()

    def compute_hash(self) -> str:
        """
        Derive the SHA-256 hash of the block's contents.

        Only the five *content* fields are hashed — the ``hash`` field itself
        is excluded to avoid a circular dependency.  ``sort_keys=True``
        guarantees the same byte-sequence regardless of dict insertion order.
        """
        block_data = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "transactions": self.transactions,
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
            },
            sort_keys=True,
        )
        return hashlib.sha256(block_data.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialise the block to a plain dictionary (for JSON storage)."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Block":
        """Reconstruct a Block from a dictionary loaded from JSON."""
        return cls(
            index=data["index"],
            transactions=data["transactions"],
            previous_hash=data["previous_hash"],
            nonce=data["nonce"],
            timestamp=data["timestamp"],
            block_hash=data["hash"],
        )
