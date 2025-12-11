from fastapi import APIRouter, HTTPException, Body, Depends
from fastapi.responses import Response
from typing import Optional
import os

from ...core.api_key_auth import require_api_key


router = APIRouter(prefix="")


@router.post("/tts")
async def tts(body: Optional[dict] = Body(None), _api_key=Depends(require_api_key)):
    """Text-to-Speech using IndicParler TTS.
    
    Parameters:
    - text: Text to convert to speech (required)
    - language: Language code (optional, 2-letter ISO 639-1, auto-detects if not provided)
    - voice_description: Description of desired voice characteristics (optional)
    - speaker: Speaker name for consistent voice (optional)
    
    Supported languages (21): as, bn, brx, en, gu, hi, kn, ks, ml, mni, mr, ne, or, pa, sa, sd, ta, te, ur, doi, kok
    
    Returns: Audio file (WAV format) with metadata in headers
    """
    try:
        if body is None:
            raise HTTPException(status_code=400, detail="Request body is required")
        
        text = body.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="'text' is required")
        
        language = body.get("language") or body.get("lang")
        voice_description = body.get("voice_description") or body.get("description")
        speaker = body.get("speaker")
        
        # Check if we should use local IndicParler TTS or external API
        use_local_tts = os.getenv("USE_LOCAL_TTS", "true").lower() == "true"
        
        if use_local_tts:
            # Use local IndicParler TTS
            from ...services.indicparler_tts import get_indicparler_tts_service
            
            try:
                indicparler_service = get_indicparler_tts_service()
                result = await indicparler_service.synthesize(
                    text=text,
                    language=language,
                    voice_description=voice_description,
                    speaker=speaker,
                )
                
                # Return audio as WAV file
                return Response(
                    content=result.audio_data,
                    media_type="audio/wav",
                    headers={
                        "X-Sample-Rate": str(result.sample_rate),
                        "X-Language": result.language,
                        "X-Model": result.model,
                        "X-Speaker": result.speaker or "default",
                        "Content-Disposition": 'attachment; filename="speech.wav"'
                    }
                )
            except (ImportError, RuntimeError) as e:
                # Fallback to AI4Bharat client if IndicParler is not available
                error_msg = str(e)
                if "IndicParler" in error_msg or "parler" in error_msg.lower():
                    raise HTTPException(
                        status_code=500,
                        detail="IndicParler TTS is not available. Please install: pip install parler-tts torch transformers soundfile"
                    )
                raise
        else:
            # Use external AI4Bharat API
            from ...services.ai4bharat import Ai4BharatClient
            client = Ai4BharatClient()
            return await client.tts(
                text=text,
                lang=language,
                speaker=speaker,
                sample_rate=body.get("sample_rate"),
                fmt=body.get("format", "wav"),
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


