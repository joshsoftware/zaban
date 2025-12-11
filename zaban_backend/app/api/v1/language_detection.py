from fastapi import APIRouter, HTTPException, Body

router = APIRouter(prefix="")


@router.post("/detect-language")
async def detect_language(body: dict = Body(...)):
    """
    Detect language from text using FastText.
    
    Parameters:
    - text: Text to detect language from (required)
    
    Returns:
    - detected_lang: Language code in BCP-47 format (e.g., hin_Deva, guj_Gujr)
    - confidence: Detection confidence score (0-1)
    - method: Detection method used (fasttext)
    """
    try:
        if not body or "text" not in body:
            raise HTTPException(status_code=400, detail="'text' is required")
        
        text = body.get("text")
        if not text or not isinstance(text, str) or not text.strip():
            raise HTTPException(status_code=400, detail="'text' must be a non-empty string")
        
        # Use language detector
        from ...services.language_detection import get_language_detector
        
        detector = get_language_detector()
        result = detector.detect_language(text)
        
        return {
            "detected_lang": result.detected_lang,
            "confidence": result.confidence,
            "method": result.method,
            "is_auto_detected": result.is_auto_detected
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

