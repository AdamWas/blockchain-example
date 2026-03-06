"""
IPFS service – uploads files to a local IPFS daemon and returns the CID.

If the IPFS node is unreachable the upload is skipped gracefully so the
rest of the system keeps working (useful during development without IPFS).
"""

import logging

from app.config import IPFS_API_URL

logger = logging.getLogger(__name__)


def upload_to_ipfs(file_bytes: bytes, filename: str = "document") -> str | None:
    """
    Upload raw bytes to IPFS and return the resulting CID.

    Returns ``None`` when the IPFS daemon is not available or the
    ``ipfshttpclient`` package is not installed.
    """
    try:
        import ipfshttpclient
    except ImportError:
        logger.warning("ipfshttpclient is not installed — skipping IPFS upload.")
        return None

    try:
        with ipfshttpclient.connect(IPFS_API_URL) as client:
            cid: str = client.add_bytes(file_bytes)
            logger.info("Uploaded %s to IPFS — CID: %s", filename, cid)
            return cid
    except ipfshttpclient.exceptions.ConnectionError:
        logger.warning("Could not connect to IPFS daemon at %s — skipping upload.", IPFS_API_URL)
        return None
    except Exception as exc:
        logger.warning("IPFS upload failed (%s: %s). Continuing without IPFS.", type(exc).__name__, exc)
        return None
