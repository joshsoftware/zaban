from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import asyncio
import base64
import os

from ...services.ai4bharat import Ai4BharatClient
from ...services.indictrans2 import get_indictrans2_service
from ...services.language_detection import get_language_detector
from ...core.api_key_auth import require_api_key


router = APIRouter(prefix="")


# BCP-47 (e.g. eng_Latn, hin_Deva) -> 2-letter code for TTS
_BCP47_TO_TTS_LANG = {
    "eng": "en", "hin": "hi", "ben": "bn", "tel": "te", "tam": "ta",
    "guj": "gu", "kan": "kn", "mal": "ml", "mar": "mr", "pan": "pa",
    "ory": "or", "asm": "as", "urd": "ur", "npi": "ne", "san": "sa",
    "kas": "ks", "gom": "kok", "mni": "mni", "snd": "sd", "sat": "sat",
    "doi": "doi", "brx": "brx", "mai": "mai",
}


def _target_lang_to_tts_lang(target_lang: str) -> str:
    """Convert BCP-47 target_lang to 2-letter TTS language code."""
    if not target_lang:
        return "en"
    base = target_lang.split("_")[0].lower()
    return _BCP47_TO_TTS_LANG.get(base, "en")


class TranslateRequest(BaseModel):
    text: str
    source_lang: Optional[str] = None  # Made optional for auto-detection
    target_lang: str
    domain: Optional[str] = None
    auto_detect: Optional[bool] = False  # Enable auto-detection
    include_audio: Optional[bool] = False  # If true, include TTS audio of translated text in response


client = Ai4BharatClient()


def _synthesize_tts_audio_sync(text: str, target_lang: str) -> tuple[bytes, int]:
    """Sync TTS (runs in thread pool). Runs async TTS in a new loop. Returns (audio_bytes, sample_rate)."""
    tts_lang = _target_lang_to_tts_lang(target_lang)
    use_local_tts = os.getenv("USE_LOCAL_TTS", "true").lower() == "true"

    async def _do_tts():
        if use_local_tts:
            from ...services.indicparler_tts import get_indicparler_tts_service
            svc = get_indicparler_tts_service()
            r = await svc.synthesize(text=text, language=tts_lang, voice_description=None, speaker=None)
            return r.audio_data, r.sample_rate
        from ...services.ai4bharat import Ai4BharatClient
        client = Ai4BharatClient()
        resp = await client.tts(text=text, lang=tts_lang, fmt="wav")
        if isinstance(resp, dict) and "audio" in resp:
            raw = resp["audio"]
            audio_bytes = base64.b64decode(raw) if isinstance(raw, str) else raw
            return audio_bytes, resp.get("sample_rate", 22050)
        if hasattr(resp, "content"):
            return resp.content, 22050
        raise HTTPException(status_code=500, detail="TTS returned unexpected format")

    return asyncio.run(_do_tts())


async def _synthesize_tts_audio(text: str, target_lang: str) -> tuple[bytes, int]:
    """TTS in thread pool so event loop is not blocked. Returns (audio_bytes, sample_rate)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _synthesize_tts_audio_sync, text, target_lang
    )


@router.post("/translate")
async def translate(req: TranslateRequest, _api_key=Depends(require_api_key)):
    """
    Translate text using IndicTrans2 model (local) or external API.
    
    Features:
    - Auto-detection of source language when source_lang is not provided
    - Support for 22 Indian languages
    - BCP-47 language codes with script (e.g., eng_Latn, hin_Deva)
    - include_audio: when true, TTS audio is included (audio_base64, audio_content_type, audio_sample_rate). To play in Postman: add the Tests script in API_QUICK_REFERENCE.md and open the response's Visualize tab.
    
    Auto-detection:
    - Set auto_detect=true to enable automatic language detection
    - Leave source_lang empty or null to use auto-detection
    - Detection uses FastText and script patterns
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
            response = {
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
                response = dict(result)
                response["model"] = "external-api"
                response["auto_detected"] = req.auto_detect and not req.source_lang
            else:
                response = {"translated_text": result, "source_lang": source_lang, "target_lang": req.target_lang, "model": "external-api", "auto_detected": req.auto_detect and not req.source_lang}
            translated_text = response.get("translated_text") or response.get("translation")
            if not isinstance(translated_text, str):
                translated_text = None

        if req.include_audio and translated_text:
            audio_bytes, sample_rate = await _synthesize_tts_audio(translated_text, req.target_lang)
            response["audio_base64"] = base64.b64encode(audio_bytes).decode("ascii")
            response["audio_content_type"] = "audio/wav"
            response["audio_sample_rate"] = sample_rate

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


