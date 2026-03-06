"""
Custom blockchain implementation.

The chain is an in-memory list of :class:`Block` objects that is persisted
to a JSON file on disk after every mutation.

Key design decisions
--------------------
* **Proof-of-work** — new blocks (including genesis) must have a hash that
  starts with ``difficulty`` leading zeros.  The miner increments the nonce
  until this condition is met.
* **Thread safety** — all reads/writes to the chain and the backing file are
  serialised through a :class:`threading.Lock` so concurrent FastAPI requests
  cannot corrupt the state.
* **Atomic persistence** — the chain is written to a temporary file first,
  then renamed over the target path.  This avoids leaving a half-written
  file if the process crashes mid-save.
* **Genesis validation** — :meth:`validate_chain` checks *every* block
  including block 0.
"""

import json
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from app.blockchain.block import Block
from app.config import BLOCKCHAIN_FILE, MINING_DIFFICULTY

logger = logging.getLogger(__name__)


class Blockchain:
    """In-memory blockchain backed by a JSON file on disk."""

    def __init__(self) -> None:
        self.chain: list[Block] = []
        self.difficulty: int = MINING_DIFFICULTY
        self._lock = threading.Lock()
        self._load_chain()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load_chain(self) -> None:
        """Load the chain from disk, or create a mined genesis block."""
        path = Path(BLOCKCHAIN_FILE)
        if path.exists():
            with open(path, "r") as fh:
                data = json.load(fh)
            self.chain = [Block.from_dict(b) for b in data]
            logger.info("Loaded blockchain with %d blocks from %s", len(self.chain), path)
        else:
            self._create_genesis_block()
            logger.info("Created new blockchain with genesis block")

    def _save_chain(self) -> None:
        """
        Atomically persist the chain to the JSON file.

        Writes to a temporary file in the same directory first, then
        renames it.  On POSIX systems ``os.replace`` is atomic.
        """
        dir_name = os.path.dirname(BLOCKCHAIN_FILE) or "."
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as fh:
                json.dump([b.to_dict() for b in self.chain], fh, indent=2)
            os.replace(tmp_path, BLOCKCHAIN_FILE)
        except BaseException:
            os.unlink(tmp_path)
            raise

    # ------------------------------------------------------------------
    # Genesis
    # ------------------------------------------------------------------

    def _create_genesis_block(self) -> None:
        """
        Create and mine block 0 (the genesis block).

        The genesis block has no transactions and a ``previous_hash``
        of ``"0"``.  It is mined like any other block so the entire
        chain consistently satisfies the difficulty target.
        """
        genesis = Block(index=0, transactions=[], previous_hash="0")
        self._mine_block(genesis)
        self.chain.append(genesis)
        self._save_chain()

    # ------------------------------------------------------------------
    # Mining / adding blocks
    # ------------------------------------------------------------------

    def get_last_block(self) -> Block:
        """Return the most recent block in the chain."""
        return self.chain[-1]

    def _mine_block(self, block: Block) -> None:
        """
        Proof-of-work: increment the nonce until the block's hash begins
        with ``self.difficulty`` leading zeros.

        Mutates *block* in place (updates ``nonce`` and ``hash``).
        """
        target = "0" * self.difficulty
        while not block.hash.startswith(target):
            block.nonce += 1
            block.hash = block.compute_hash()
        logger.debug(
            "Mined block %d  nonce=%d  hash=%s",
            block.index, block.nonce, block.hash,
        )

    def add_block(self, transactions: list[dict[str, Any]]) -> Block:
        """
        Create, mine, and append a new block.

        The entire operation is protected by a lock so concurrent API
        requests are serialised.
        """
        with self._lock:
            last = self.get_last_block()
            new_block = Block(
                index=last.index + 1,
                transactions=transactions,
                previous_hash=last.hash,
            )
            self._mine_block(new_block)
            self.chain.append(new_block)
            self._save_chain()
            logger.info("Added block %d with %d transaction(s)", new_block.index, len(transactions))
            return new_block

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_chain(self) -> tuple[bool, str]:
        """
        Walk the full chain and verify integrity.

        Checks performed on **every** block (including genesis):

        1. The stored ``hash`` matches a freshly computed hash.
        2. The hash satisfies the proof-of-work difficulty target.

        Additional check for blocks after genesis:

        3. ``previous_hash`` equals the preceding block's ``hash``.

        Returns a ``(valid, message)`` tuple so callers can surface a
        human-readable explanation on failure.
        """
        if not self.chain:
            return False, "Chain is empty."

        target = "0" * self.difficulty

        for i, block in enumerate(self.chain):
            recomputed = block.compute_hash()
            if block.hash != recomputed:
                msg = (
                    f"Block {i}: stored hash does not match computed hash "
                    f"(stored={block.hash!r}, computed={recomputed!r})."
                )
                logger.warning(msg)
                return False, msg

            if not block.hash.startswith(target):
                msg = f"Block {i}: hash does not meet difficulty target ({target}…)."
                logger.warning(msg)
                return False, msg

            if i > 0:
                previous = self.chain[i - 1]
                if block.previous_hash != previous.hash:
                    msg = (
                        f"Block {i}: previous_hash mismatch "
                        f"(expected={previous.hash!r}, got={block.previous_hash!r})."
                    )
                    logger.warning(msg)
                    return False, msg

        return True, "Blockchain is valid."

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def find_transaction(self, transaction_id: str) -> dict[str, Any] | None:
        """Search every block for a transaction with the given id."""
        for block in self.chain:
            for tx in block.transactions:
                if tx.get("transaction_id") == transaction_id:
                    return tx
        return None

    def find_block_by_index(self, index: int) -> Block | None:
        """Return a block by its index, or ``None``."""
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None

    def to_dict_list(self) -> list[dict[str, Any]]:
        """Return the full chain as a list of serialisable dicts."""
        return [b.to_dict() for b in self.chain]
