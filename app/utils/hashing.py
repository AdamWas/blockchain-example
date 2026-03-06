"""
Hashing utilities.

Provides a single source of truth for the SHA-256 computation used
throughout the application (certificate issuance, verification, etc.).
"""

import hashlib


def sha256_hash(data: bytes) -> str:
    """Return the hex-encoded SHA-256 digest of *data*."""
    return hashlib.sha256(data).hexdigest()
