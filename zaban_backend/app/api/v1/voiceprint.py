"""API routes for voiceprint operations."""

import os
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.voiceprint import Voiceprint, VerificationAttempt, VoiceprintUser
from app.schemas.voiceprint import (
    EnrollmentResponse,
    VerificationResponse,
    VoiceprintResponse,
    VoiceprintUpdateRequest,
    VoiceprintUpdateResponse,
    VerificationAttemptResponse,
    UserListResponse,
    UserInfo
)
from app.services.voiceprint.config import voiceprint_settings as settings
from app.services.voiceprint.utils.xor_cipher import decrypt_audio_base64

router = APIRouter(prefix="/voiceprint", tags=["voiceprint"])


def get_verifier(request: Request):
    """Dependency to get the voice verifier from app state."""
    if not settings.VOICEPRINT_ENABLED:
        raise HTTPException(status_code=501, detail="Voiceprint service is disabled")
    
    verifier = getattr(request.app.state, "voice_verifier", None)
    if verifier is None:
        raise HTTPException(status_code=503, detail="Voiceprint service not initialized")
    return verifier


@router.post("/enroll/{user_id}", response_model=EnrollmentResponse)
async def enroll_voiceprint(
    user_id: str,
    device_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    verifier=Depends(get_verifier)
):
    """Enroll a user's voiceprint with multiple audio samples."""
    # Check if voiceprint user exists, if not create one (if strict or device_id provided)
    vp_user = db.query(VoiceprintUser).filter(VoiceprintUser.user_id == str(user_id)).first()
    if not vp_user:
        if settings.STRICT_VOICEPRINT_USER_CHECK or device_id:
            vp_user = VoiceprintUser(user_id=str(user_id), device_id=device_id)
            db.add(vp_user)
            db.commit()
    elif device_id and vp_user.device_id != device_id:
        vp_user.device_id = device_id
        db.commit()

    if len(files) < settings.MIN_ENROLLMENT_SAMPLES:
        raise HTTPException(
            status_code=400, 
            detail=f"At least {settings.MIN_ENROLLMENT_SAMPLES} audio samples required"
        )
    
    # Process files
    audio_data = []
    temp_files = []
    try:
        for file in files:
            content = await file.read()
            # Save to temp file for processing
            temp_path = f"/tmp/{user_id}_{file.filename}"
            with open(temp_path, "wb") as f:
                f.write(content)
            temp_files.append(temp_path)
            audio_data.append(temp_path)

        # Enroll in vector store
        result = verifier.enroll_user(audio_data, str(user_id))
        
        # Create DB record
        # Set other voiceprints for this user to inactive
        db.query(Voiceprint).filter(Voiceprint.user_id == str(user_id)).update({"is_active": False})
        
        # Retrieve vector ID - verifier.enroll_user doesn't return it currently, 
        
        # TODO: Refactor verifier to accept/return vector_id if needed.
        # using placeholder UUID since verifier uses user_id as key in Qdrant.
        import uuid
        vector_id = uuid.uuid4() 
        
        new_vp = Voiceprint(
            user_id=str(user_id),
            qdrant_vector_id=vector_id,
            model_name=settings.ECAPA_SOURCE,
            is_active=True
        )
        db.add(new_vp)
        db.commit()
        db.refresh(new_vp)
        
        return EnrollmentResponse(
            status="success",
            user_id=user_id,
            device_id=vp_user.device_id if vp_user else None,
            message="Voiceprint enrolled successfully",
            num_samples=len(files)
        )
    finally:
        # Cleanup temp files
        for path in temp_files:
            if os.path.exists(path):
                os.remove(path)


@router.post("/verify/{user_id}", response_model=VerificationResponse)
async def verify_voiceprint(
    user_id: str,
    file: UploadFile = File(None),
    encrypted_audio: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    verifier=Depends(get_verifier)
):
    """Verify a user's voice against their enrolled voiceprint."""
    # Check if user exists (if strict check is enabled)
    if settings.STRICT_VOICEPRINT_USER_CHECK:
        vp_user = db.query(VoiceprintUser).filter(VoiceprintUser.user_id == str(user_id)).first()
        if not vp_user:
            raise HTTPException(status_code=404, detail="Voiceprint user not found")

    # Get active voiceprint
    voiceprint = db.query(Voiceprint).filter(
        Voiceprint.user_id == str(user_id), 
        Voiceprint.is_active == True
    ).first()
    
    if not voiceprint:
        raise HTTPException(status_code=400, detail="No active voiceprint found for user")

    # Get audio content
    if file:
        audio_content = await file.read()
    elif encrypted_audio:
        try:
            audio_content = decrypt_audio_base64(encrypted_audio, settings.XOR_AUDIO_KEY)
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to decrypt audio")
    else:
        raise HTTPException(status_code=400, detail="No audio provided")

    temp_path = f"/tmp/verify_{user_id}.wav"
    try:
        with open(temp_path, "wb") as f:
            f.write(audio_content)

        # Verify
        result = verifier.verify_speaker(temp_path, str(user_id))
        
        if result.get("error"):
            return VerificationResponse(
                verified=False,
                threshold=settings.VERIFICATION_THRESHOLD,
                error=result["error"]
            )

        # Log attempt
        import uuid
        attempt = VerificationAttempt(
            user_id=str(user_id),
            voiceprint_id=voiceprint.id,
            probe_qdrant_vector_id=uuid.uuid4(), # Placeholder
            raw_plda_score=result["raw_score"],
            as_norm_score=result["score"],
            threshold=result["threshold"],
            decision="accept" if result["verified"] else "reject"
        )
        db.add(attempt)
        db.commit()

        from app.schemas.voiceprint import CohortStatistics
        cohort_stats = CohortStatistics(
            enrollment_cohort_mean=result["enrollment_cohort_mean"],
            enrollment_cohort_std=result["enrollment_cohort_std"],
            test_cohort_mean=result["test_cohort_mean"],
            test_cohort_std=result["test_cohort_std"],
            cohort_size=result["cohort_size"]
        )

        return VerificationResponse(
            verified=result["verified"],
            score=result["score"],
            raw_score=result["raw_score"],
            threshold=result["threshold"],
            cohort_stats=cohort_stats
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/{user_id}/voiceprints", response_model=List[VoiceprintResponse])
async def list_user_voiceprints(user_id: str, db: Session = Depends(get_db)):
    """List all voiceprints for a user."""
    voiceprints = db.query(Voiceprint).filter(Voiceprint.user_id == str(user_id)).all()
    return voiceprints


@router.patch("/{voiceprint_id}", response_model=VoiceprintUpdateResponse)
async def update_voiceprint(
    voiceprint_id: str, 
    request: VoiceprintUpdateRequest, 
    db: Session = Depends(get_db)
):
    """Activate or deactivate a voiceprint."""
    vp = db.query(Voiceprint).filter(Voiceprint.id == voiceprint_id).first()
    if not vp:
        raise HTTPException(status_code=404, detail="Voiceprint not found")

    if request.is_active:
        # Deactivate others for this user
        db.query(Voiceprint).filter(
            Voiceprint.user_id == vp.user_id, 
            Voiceprint.id != voiceprint_id
        ).update({"is_active": False})
    
    vp.is_active = request.is_active
    db.commit()
    
    return VoiceprintUpdateResponse(
        voiceprint_id=voiceprint_id,
        is_active=vp.is_active,
        message=f"Voiceprint {'activated' if vp.is_active else 'deactivated'} successfully"
    )


@router.delete("/{voiceprint_id}")
async def delete_voiceprint(
    voiceprint_id: UUID, 
    db: Session = Depends(get_db),
    verifier=Depends(get_verifier)
):
    """Delete a voiceprint."""
    vp = db.query(Voiceprint).filter(Voiceprint.id == voiceprint_id).first()
    if not vp:
        raise HTTPException(status_code=404, detail="Voiceprint not found")

    # Note: verifier.delete_user uses user_id. If multiple VPs exist
    user_id = str(vp.user_id)
    
    db.delete(vp)
    db.commit()
    
    # Check if any other VPs exist for this user before deleting from vector store
    remaining = db.query(Voiceprint).filter(Voiceprint.user_id == vp.user_id).count()
    if remaining == 0:
        verifier.delete_user(user_id)
    
    return {"status": "success", "message": "Voiceprint deleted"}


@router.get("/verify/{user_id}/history", response_model=List[VerificationAttemptResponse])
async def get_verification_history(user_id: str, db: Session = Depends(get_db)):
    """Get verification attempt history for a user."""
    attempts = db.query(VerificationAttempt).filter(
        VerificationAttempt.user_id == str(user_id)
    ).order_by(VerificationAttempt.created_at.desc()).all()
    return attempts


@router.get("/health")
async def voiceprint_health(verifier=Depends(get_verifier)):
    """Check if the voiceprint service (Qdrant) is reachable."""
    try:
        collections = verifier.qdrant_client.get_collections()
        return {
            "status": "healthy",
            "qdrant_connected": True,
            "collections": [c.name for c in collections.collections]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "qdrant_connected": False,
            "error": str(e)
        }
