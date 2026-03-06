"""
Verification service – confirms that a certificate exists in both the
database and the blockchain **and** that the containing block has not
been tampered with.
"""

import logging

from sqlalchemy.orm import Session

from app.models.certificate import Certificate
from app.schemas.verification import VerificationResponse
from app.services import blockchain_service, certificate_service
from app.utils.hashing import sha256_hash

logger = logging.getLogger(__name__)


def _verify_certificate(cert: Certificate) -> VerificationResponse:
    """
    Shared verification logic once we have a database record.

    1. Look up the transaction on the blockchain.
    2. Verify the containing block's hash matches its contents.
    3. Check the chain link (``previous_hash``) is intact.
    """
    tx = blockchain_service.find_transaction(cert.transaction_id)
    if tx is None:
        logger.warning(
            "Certificate %s exists in DB but transaction %s not found on chain",
            cert.certificate_id, cert.transaction_id,
        )
        return VerificationResponse(
            verified=False,
            message="Certificate exists in the database but its transaction is missing from the blockchain.",
            certificate_id=cert.certificate_id,
            document_hash=cert.document_hash,
        )

    chain = blockchain_service.get_blockchain()
    block = chain.find_block_by_index(cert.block_index)
    if block is None or block.hash != block.compute_hash():
        logger.warning("Block %d integrity check failed", cert.block_index)
        return VerificationResponse(
            verified=False,
            message="The blockchain block containing this certificate has been tampered with.",
            certificate_id=cert.certificate_id,
            document_hash=cert.document_hash,
            block_index=cert.block_index,
            transaction_id=cert.transaction_id,
        )

    if cert.block_index > 0:
        prev_block = chain.find_block_by_index(cert.block_index - 1)
        if prev_block is None or block.previous_hash != prev_block.hash:
            logger.warning("Chain link broken at block %d", cert.block_index)
            return VerificationResponse(
                verified=False,
                message="Blockchain chain-link integrity check failed for this certificate's block.",
                certificate_id=cert.certificate_id,
                document_hash=cert.document_hash,
                block_index=cert.block_index,
                transaction_id=cert.transaction_id,
            )

    logger.info("Certificate %s verified successfully", cert.certificate_id)
    return VerificationResponse(
        verified=True,
        message="Certificate is valid and recorded on the blockchain.",
        certificate_id=cert.certificate_id,
        document_hash=cert.document_hash,
        block_index=cert.block_index,
        transaction_id=cert.transaction_id,
    )


def verify_by_file(file_bytes: bytes, db: Session) -> VerificationResponse:
    """
    Verify a certificate by re-computing the SHA-256 hash of an uploaded
    file and checking it against the database and blockchain.
    """
    document_hash = sha256_hash(file_bytes)
    cert = certificate_service.get_certificate_by_hash(document_hash, db)

    if cert is None:
        return VerificationResponse(
            verified=False,
            message="No certificate found matching the uploaded document.",
            document_hash=document_hash,
        )

    return _verify_certificate(cert)


def verify_by_id(certificate_id: str, db: Session) -> VerificationResponse:
    """
    Verify a certificate by its UUID – confirms it exists in the database
    and that the corresponding blockchain block is intact.
    """
    cert = certificate_service.get_certificate_by_id(certificate_id, db)

    if cert is None:
        return VerificationResponse(
            verified=False,
            message="No certificate found with the given ID.",
            certificate_id=certificate_id,
        )

    return _verify_certificate(cert)
