"""
SQLAlchemy model for the Certificate table.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime

from app.database import Base


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(String, unique=True, index=True, nullable=False)
    student_name = Column(String, nullable=False)
    student_email = Column(String, nullable=True)
    course_name = Column(String, nullable=False)
    issuer_name = Column(String, nullable=False)
    issue_date = Column(String, nullable=False)
    document_hash = Column(String, nullable=False, index=True)
    ipfs_cid = Column(String, nullable=True)
    block_index = Column(Integer, nullable=False)
    transaction_id = Column(String, unique=True, nullable=False)
    status = Column(String, default="issued")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
