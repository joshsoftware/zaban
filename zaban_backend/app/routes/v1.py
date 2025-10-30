import os
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi import Body
from pydantic import BaseModel

from ..services.ai4bharat import Ai4BharatClient
from ..services.indictrans2 import get_indictrans2_service
from ..services.language_detection import get_language_detector


router = APIRouter()


class TtsRequest(BaseModel):
    text: str
    lang: str
    speaker: Optional[str] = None
    sample_rate: Optional[int] = None
    format: Optional[str] = "wav"


class TranslateRequest(BaseModel):
    text: str
    source_lang: Optional[str] = None  # Made optional for auto-detection
    target_lang: str
    domain: Optional[str] = None
    auto_detect: Optional[bool] = False  # Enable auto-detection


class TransliterateRequest(BaseModel):
    text: str
    source_script: str
    target_script: str
    lang: str
    topk: Optional[int] = 1


client = Ai4BharatClient()


@router.post("/tts")
async def tts(req: TtsRequest):
    try:
        return await client.tts(text=req.text, lang=req.lang, speaker=req.speaker, sample_rate=req.sample_rate, fmt=req.format)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stt")
async def stt(
    audio: Optional[UploadFile] = File(None),
    lang: Optional[str] = Form(None),
    format: Optional[str] = Form(None),
    body: Optional[dict] = Body(None)
):
    try:
        if audio is not None:
            if not lang:
                raise HTTPException(status_code=400, detail="lang is required for multipart upload")
            return await client.stt_file(audio=audio, lang=lang, fmt=format)
        if body is None:
            raise HTTPException(status_code=400, detail="Provide multipart with audio or JSON with audio_url")
        audio_url = body.get("audio_url")
        lang_json = body.get("lang")
        fmt_json = body.get("format")
        if not audio_url or not lang_json:
            raise HTTPException(status_code=400, detail="audio_url and lang are required")
        return await client.stt_url(audio_url=audio_url, lang=lang_json, fmt=fmt_json)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/translate")
async def translate(req: TranslateRequest):
    """
    Translate text using IndicTrans2 model (local) or external API.
    
    Features:
    - Auto-detection of source language when source_lang is not provided
    - Support for 22 Indian languages
    - BCP-47 language codes with script (e.g., eng_Latn, hin_Deva)
    
    Auto-detection:
    - Set auto_detect=true to enable automatic language detection
    - Leave source_lang empty or null to use auto-detection
    - Detection uses FastText and script patterns
    
    Request Examples:
    {
      "text": "How are you?",
      "source_lang": "eng_Latn",  # Explicit source language
      "target_lang": "hin_Deva"
    }
    
    {
      "text": "नमस्ते दुनिया",
      "target_lang": "eng_Latn",
      "auto_detect": true  # Auto-detect source language
    }
    
    Response:
    {
      "translated_text": "आप कैसे हैं?",
      "source_lang": "eng_Latn",
      "target_lang": "hin_Deva",
      "model": "indictrans2-local",
      "auto_detected": true
    }
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
        
        # Check if we should use local IndicTrans2 model or external API
        use_local = os.getenv("USE_LOCAL_INDICTRANS2", "true").lower() == "true"
        
        if use_local:
            # Use local IndicTrans2 model
            indictrans_service = get_indictrans2_service()
            # Guard: IndicTrans2 supports only Indic languages + English
            supported_indic = get_language_detector()._get_supported_indic_languages()
            if source_lang not in supported_indic:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported source language for IndicTrans2: {source_lang}. Supported: {', '.join(supported_indic)}"
                )
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
        # (No else case for international/external)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transliterate")
async def transliterate(req: TransliterateRequest):
    try:
        return await client.transliterate(text=req.text, source_script=req.source_script, target_script=req.target_script, lang=req.lang, topk=req.topk)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


