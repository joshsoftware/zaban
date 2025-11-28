from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

from ...services.accent_detection import AccentDetectionService
from fastapi import Depends

router = APIRouter(prefix="")

class AccentDetectResponse(BaseModel):
    accent: str
    confidence: float
    details: Optional[dict] = None



def get_accent_detection_service():
    return AccentDetectionService()

@router.post("/accent-detect", response_model=AccentDetectResponse)
async def accent_detect(
    audio: UploadFile = File(...),
    service: AccentDetectionService = Depends(get_accent_detection_service)
):
    try:
        result = await service.detect_accent(audio)
        return AccentDetectResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
