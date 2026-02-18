"""Pydantic schemas for voiceprint operations."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Enrollment Schemas
class EnrollmentResponse(BaseModel):
    """Response model for enrollment endpoint."""
    status: str = Field(..., description="Status of the enrollment operation")
    customer_id: str = Field(..., description="Customer unique identifier")
    device_id: Optional[str] = Field(None, description="Device unique identifier")
    message: str = Field(..., description="Human-readable message")
    num_samples: Optional[int] = Field(None, description="Number of audio samples used")


class UserInfo(BaseModel):
    """Simplified user info for lists."""
    customer_id: str
    device_id: Optional[str] = None
    num_samples: Optional[int] = None


class UserListResponse(BaseModel):
    """Response model for listing enrolled users in vector store."""
    users: List[UserInfo]
    count: int


# Verification Schemas
class CohortStatistics(BaseModel):
    """Cohort statistics from AS-Norm computation."""
    enrollment_cohort_mean: float
    enrollment_cohort_std: float
    test_cohort_mean: float
    test_cohort_std: float
    cohort_size: int


class VerificationResponse(BaseModel):
    """Response model for verification endpoint."""
    verified: bool = Field(..., description="Whether the speaker was verified")
    score: Optional[float] = Field(None, description="AS-Norm score")
    raw_score: Optional[float] = Field(None, description="Raw PLDA score before normalization")
    threshold: float = Field(..., description="Verification threshold used")
    cohort_stats: Optional[CohortStatistics] = Field(None, description="Cohort statistics")
    error: Optional[str] = Field(None, description="Error message if any")


# Voiceprint Management Schemas
class VoiceprintResponse(BaseModel):
    """Response model for voiceprint object."""
    id: UUID
    customer_id: str
    qdrant_vector_id: int
    is_active: bool
    verification: bool
    last_verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VoiceprintUpdateRequest(BaseModel):
    """Request model for updating a voiceprint."""
    is_active: bool = Field(..., description="Set voiceprint active/inactive")


class VoiceprintUpdateResponse(BaseModel):
    """Response model for voiceprint update."""
    voiceprint_id: UUID
    is_active: bool
    message: str


class VerificationAttemptResponse(BaseModel):
    """Response model for verification attempt log entry."""
    id: UUID
    voiceprint_id: UUID
    raw_plda_score: float
    as_norm_score: float
    threshold: float
    count: int
    created_at: datetime

    class Config:
        from_attributes = True
