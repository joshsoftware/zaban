"""API routes for voiceprint operations."""

import os
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.voiceprint import Voiceprint, VerificationAttempt
from app.schemas.voiceprint import (
    EnrollmentResponse,
    VerificationResponse,
    VoiceprintUpdateRequest,
    VoiceprintUpdateResponse,
    VerificationAttemptResponse,
)
from app.services.voiceprint.config import voiceprint_settings as settings
from app.services.voiceprint.utils.xor_cipher import decrypt_audio_bytes

router = APIRouter(prefix="/voiceprint", tags=["voiceprint"])


def get_verifier(request: Request):
    """Dependency to get the voice verifier from app state.
    
    Returns None with a reason message if the service is unavailable,
    instead of raising an exception.
    """
    if not settings.VOICEPRINT_ENABLED:
        return None
    
    verifier = getattr(request.app.state, "voice_verifier", None)
    return verifier


def _service_unavailable_response() -> JSONResponse:
    """Return a graceful response when voiceprint service is unavailable."""
    if not settings.VOICEPRINT_ENABLED:
        msg = "Voiceprint service is disabled"
    else:
        msg = "Voiceprint service is not initialized"
    return JSONResponse(
        status_code=503,
        content={"status": "unavailable", "message": msg}
    )


@router.post("/enroll", response_model=EnrollmentResponse)
async def enroll_voiceprint(
    customer_id: str = Form(...),
    device_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    verifier=Depends(get_verifier)
):
    """Enroll a user's voiceprint with multiple audio samples.
    
    One user can have only one voiceprint. If a voiceprint already exists
    for this customer_id, it will be replaced.
    """
    if verifier is None:
        return _service_unavailable_response()
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
            # Decrypt if encryption is enabled
            if settings.AUDIO_ENCRYPTION_ENABLED:
                try:
                    content = decrypt_audio_bytes(content, settings.XOR_AUDIO_KEY)
                except Exception:
                    raise HTTPException(status_code=400, detail="Failed to decrypt audio file")
            # Save to temp file for processing
            temp_path = f"/tmp/{customer_id}_{file.filename}"
            with open(temp_path, "wb") as f:
                f.write(content)
            temp_files.append(temp_path)
            audio_data.append(temp_path)

        # Enroll in vector store
        result = verifier.enroll_user(audio_data, str(customer_id))
        
        # One user = one voiceprint: remove existing voiceprint if any
        existing_vp = db.query(Voiceprint).filter(Voiceprint.customer_id == str(customer_id)).first()
        if existing_vp:
            db.delete(existing_vp)
            db.flush()
        
        # Create new voiceprint record
        new_vp = Voiceprint(
            customer_id=str(customer_id),
            qdrant_vector_id=result["point_id"],
            is_active=True
        )

        db.add(new_vp)
        db.commit()
        db.refresh(new_vp)
        
        return EnrollmentResponse(
            status="success",
            customer_id=customer_id,
            device_id=device_id,
            message="Voiceprint enrolled successfully",
            num_samples=len(files)
        )
    finally:
        # Cleanup temp files
        for path in temp_files:
            if os.path.exists(path):
                os.remove(path)


@router.post("/verify", response_model=VerificationResponse)
async def verify_voiceprint(
    customer_id: str = Form(...),
    device_id: Optional[str] = Form(None),
    file: UploadFile = File(None),
    encrypted_audio: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    verifier=Depends(get_verifier)
):
    """Verify a user's voice against their enrolled voiceprint."""
    if verifier is None:
        return _service_unavailable_response()
    # Get active voiceprint
    voiceprint = db.query(Voiceprint).filter(
        Voiceprint.customer_id == str(customer_id), 
        Voiceprint.is_active == True
    ).first()
    
    if not voiceprint:
        raise HTTPException(status_code=400, detail="No active voiceprint found for user")

    # Get audio content
    if file:
        audio_content = await file.read()
        # Decrypt if encryption is enabled
        if settings.AUDIO_ENCRYPTION_ENABLED:
            try:
                audio_content = decrypt_audio_bytes(audio_content, settings.XOR_AUDIO_KEY)
            except Exception:
                raise HTTPException(status_code=400, detail="Failed to decrypt audio")
    elif encrypted_audio:
        # Legacy support: explicit encrypted_audio field (always decrypted)
        try:
            audio_content = decrypt_audio_bytes(encrypted_audio, settings.XOR_AUDIO_KEY)
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to decrypt audio")
    else:
        raise HTTPException(status_code=400, detail="No audio provided")

    temp_path = f"/tmp/verify_{customer_id}.wav"
    try:
        with open(temp_path, "wb") as f:
            f.write(audio_content)

        # Verify
        result = verifier.verify_speaker(temp_path, str(customer_id))
        
        if result.get("error"):
            return VerificationResponse(
                verified=False,
                threshold=settings.VERIFICATION_THRESHOLD,
                error=result["error"]
            )

        is_verified = result["verified"]

        # Log attempt
        attempt = VerificationAttempt(
            voiceprint_id=voiceprint.id,
            raw_plda_score=result["raw_score"],
            as_norm_score=result["score"],
            threshold=result["threshold"],
        )
        db.add(attempt)

        # Update voiceprint verification status
        if is_verified:
            from datetime import datetime, timezone
            voiceprint.verification = True
            voiceprint.last_verified_at = datetime.now(timezone.utc)

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
            verified=is_verified,
            score=result["score"],
            raw_score=result["raw_score"],
            threshold=result["threshold"],
            cohort_stats=cohort_stats
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)



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
        # Deactivate others for this customer
        db.query(Voiceprint).filter(
            Voiceprint.customer_id == vp.customer_id, 
            Voiceprint.id != voiceprint_id
        ).update({"is_active": False})
    
    vp.is_active = request.is_active
    db.commit()
    
    return VoiceprintUpdateResponse(
        voiceprint_id=voiceprint_id,
        is_active=vp.is_active,
        message=f"Voiceprint {'activated' if vp.is_active else 'deactivated'} successfully"
    )


@router.delete("/")
async def delete_voiceprint(
    customer_id: str = Form(...), 
    db: Session = Depends(get_db),
    verifier=Depends(get_verifier)
):
    """Delete a voiceprint."""
    if verifier is None:
        return _service_unavailable_response()
    vp = db.query(Voiceprint).filter(Voiceprint.customer_id == customer_id).first()
    if not vp:
        raise HTTPException(status_code=404, detail="Voiceprint not found")
    
    db.delete(vp)
    db.commit()
    
    # Check if any other VPs exist for this customer before deleting from vector store
    remaining = db.query(Voiceprint).filter(Voiceprint.customer_id == customer_id).count()
    if remaining == 0:
        verifier.delete_user(customer_id)
    
    return {"status": "success", "message": "Voiceprint deleted"}


@router.get("/verify/{customer_id}/history", response_model=List[VerificationAttemptResponse])
async def get_verification_history(customer_id: str, db: Session = Depends(get_db)):
    """Get verification attempt history for a customer."""
    voiceprint = db.query(Voiceprint).filter(
        Voiceprint.customer_id == str(customer_id)
    ).first()

    if not voiceprint:
        raise HTTPException(status_code=404, detail="Voiceprint not found for this customer")

    attempts = db.query(VerificationAttempt).filter(
        VerificationAttempt.voiceprint_id == voiceprint.id
    ).order_by(VerificationAttempt.created_at.desc()).all()
    return attempts


@router.get("/health")
async def voiceprint_health(verifier=Depends(get_verifier)):
    """Check if the voiceprint service (Qdrant) is reachable."""
    if verifier is None:
        return _service_unavailable_response()
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
