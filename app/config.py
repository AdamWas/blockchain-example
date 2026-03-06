"""
Application configuration.

Centralizes all settings so they can be changed in one place.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'certificates.db'}")

BLOCKCHAIN_FILE = os.getenv("BLOCKCHAIN_FILE", str(BASE_DIR / "blockchain.json"))

IPFS_API_URL = os.getenv("IPFS_API_URL", "/ip4/127.0.0.1/tcp/5001")

MINING_DIFFICULTY = int(os.getenv("MINING_DIFFICULTY", "2"))
