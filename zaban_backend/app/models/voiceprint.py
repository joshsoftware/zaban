import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship

from app.db.database import Base


class Voiceprint(Base):
    """
    Voiceprint model - links a customer to a Qdrant vector.

    One customer can have only one voiceprint.
    The actual embedding is stored in Qdrant, referenced by qdrant_vector_id.
    """
    __tablename__ = "voiceprints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(255), unique=True, nullable=False, index=True)
    qdrant_vector_id = Column(BigInteger, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    verification = Column(Boolean, nullable=False, default=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Partial index for active voiceprint lookup
    __table_args__ = (
        Index(
            "idx_voiceprints_active",
            "customer_id",
            "is_active",
            postgresql_where=(is_active == True),
        ),
    )

    def __repr__(self) -> str:
        return f"<Voiceprint {self.id} customer={self.customer_id} active={self.is_active}>"


class VerificationAttempt(Base):
    """
    Verification attempt model - audit log of all verification attempts.

    Stores both raw PLDA and AS-Norm scores for analysis.
    Tracks the number of verification attempts via the count column.
    """
    __tablename__ = "verification_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voiceprint_id = Column(UUID(as_uuid=True), ForeignKey("voiceprints.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_plda_score = Column(Float, nullable=False)
    as_norm_score = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    voiceprint = relationship("Voiceprint", backref=backref("verification_attempts", passive_deletes=True))

    def __repr__(self) -> str:
        return f"<VerificationAttempt {self.id} voiceprint={self.voiceprint_id} count={self.count}>"
