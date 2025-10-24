from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import os

from ...services.ai4bharat import Ai4BharatClient
from ...services.indictrans2 import get_indictrans2_service
from ...services.language_detection import get_language_detector
from ...core.api_key_auth import require_api_key


router = APIRouter(prefix="")


class TranslateRequest(BaseModel):
    text: str
    source_lang: Optional[str] = None  # Made optional for auto-detection
    target_lang: str
    domain: Optional[str] = None
    auto_detect: Optional[bool] = False  # Enable auto-detection


client = Ai4BharatClient()


@router.post("/translate")
async def translate(req: TranslateRequest, _api_key=Depends(require_api_key)):
    """
    Translate text using IndicTrans2 model (local) or external API.
    
    Features:
    - Auto-detection of source language when source_lang is not provided
    - Support for 22 Indian languages
    - BCP-47 language codes with script (e.g., eng_Latn, hin_Deva)
    
    Auto-detection:
    - Set auto_detect=true to enable automatic language detection
    - Leave source_lang empty or null to use auto-detection
    - Detection uses script patterns and common words
    """
    try:
        # Determine source language
        source_lang = req.source_lang
        
        # Auto-detect source language if not provided or auto_detect is enabled
        if not source_lang or req.auto_detect:
            detector = get_language_detector()
            detection_result = detector.detect_language(req.text)
            source_lang = detection_result.detected_lang
            
            # If auto-detection confidence is too low, default to English
            if detection_result.confidence < 0.1:
                source_lang = "eng_Latn"
        
        # Validate that we have a source language
        if not source_lang:
            raise HTTPException(
                status_code=400, 
                detail="Source language is required. Provide source_lang or enable auto_detect."
            )
        
        use_local = os.getenv("USE_LOCAL_INDICTRANS2", "true").lower() == "true"
        
        if use_local:
            indictrans_service = get_indictrans2_service()
            translated_text = await indictrans_service.translate(
                text=req.text,
                source_lang=source_lang,
                target_lang=req.target_lang
            )
            return {
                "translated_text": translated_text,
                "source_lang": source_lang,
                "target_lang": req.target_lang,
                "model": "indictrans2-local",
                "auto_detected": req.auto_detect and not req.source_lang
            }
        else:
            result = await client.translate(
                text=req.text,
                source_lang=source_lang,
                target_lang=req.target_lang,
                domain=req.domain
            )
            if isinstance(result, dict):
                result["model"] = "external-api"
                result["auto_detected"] = req.auto_detect and not req.source_lang
            return result
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


