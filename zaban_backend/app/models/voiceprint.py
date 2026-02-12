import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class Voiceprint(Base):
    """
    Voiceprint model - links user to Qdrant vector.
    
    Only one voiceprint can be active per user at any time.
    The actual embedding is stored in Qdrant, referenced by qdrant_vector_id.
    """
    __tablename__ = "voiceprints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    qdrant_vector_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    model_name = Column(String(100), nullable=False, default="ecapa-tdnn-voxceleb")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", backref="voiceprints")

    # Partial index for active voiceprint lookup
    __table_args__ = (
        Index(
            "idx_voiceprints_active",
            "user_id",
            "is_active",
            postgresql_where=(is_active == True),
        ),
    )

    def __repr__(self) -> str:
        return f"<Voiceprint {self.id} user={self.user_id} active={self.is_active}>"


class VerificationAttempt(Base):
    """
    Verification attempt model - audit log of all verification attempts.
    
    Stores both raw PLDA and AS-Norm scores for analysis.
    Probe embedding stored in Qdrant, referenced by probe_qdrant_vector_id.
    """
    __tablename__ = "verification_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    voiceprint_id = Column(UUID(as_uuid=True), ForeignKey("voiceprints.id", ondelete="CASCADE"), nullable=False, index=True)
    probe_qdrant_vector_id = Column(UUID(as_uuid=True), nullable=False)
    raw_plda_score = Column(Float, nullable=False)
    as_norm_score = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    decision = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User", backref="verification_attempts")
    voiceprint = relationship("Voiceprint", backref="verification_attempts")

    def __repr__(self) -> str:
        return f"<VerificationAttempt {self.id} decision={self.decision}>"
