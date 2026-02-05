import os
import base64
import httpx
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi import Body
from pydantic import BaseModel

from ..services.ai4bharat import Ai4BharatClient
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
        from ..services.language_detection import get_language_detector
        
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


@router.post("/tts")
async def tts(body: Optional[dict] = Body(None)):
    """Text-to-Speech using IndicParler TTS.
    
    Parameters:
    - text: Text to convert to speech (required)
    - language: Language code (optional, 2-letter ISO 639-1, auto-detects if not provided)
    - voice_description: Description of desired voice characteristics (optional)
    - speaker: Speaker name for consistent voice (optional)
    
    Supported languages (21): as, bn, brx, en, gu, hi, kn, ks, ml, mni, mr, ne, or, pa, sa, sd, ta, te, ur, doi, kok
    
    Returns: Audio file (WAV format) with metadata in headers
    """
    from fastapi.responses import Response
    
    try:
        if body is None:
            raise HTTPException(status_code=400, detail="Request body is required")
        
        text = body.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="'text' is required")
        
        language = body.get("language") or body.get("lang")
        voice_description = body.get("voice_description") or body.get("description")
        speaker = body.get("speaker")
        
        # Use IndicParler TTS
        from ..services.indicparler_tts import get_indicparler_tts_service
        
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stt")
async def stt(
    audio: Optional[UploadFile] = File(None),
    lang: Optional[str] = Form(None),
    model: Optional[str] = Form("whisper"),
    format: Optional[str] = Form(None),
    body: Optional[dict] = Body(None),
    *,
    translate_to_english: bool = False,
):
    """Speech-to-Text with model selection.

    Parameters:
    - audio: Audio file (supports WAV, MP3, M4A, WebM, OGG, FLAC, etc.)
    - lang: Language code (optional, auto-detected if not provided)
    - model: STT model to use - "whisper" (default) or "ai4bharat"
    - format: Output format (optional)

    Models:
    - whisper: faster-whisper (4-5x faster than OpenAI Whisper, supports 100+ languages)
    - ai4bharat: Vistaar IndicWhisper (best WER for Indian languages: hi, mr, ta, te, bn, gu, kn, ml, pa, or, sa, ur)
    
    Behavior:
    - If lang not provided: faster-whisper auto-detects language
    - If model=ai4bharat: Uses faster-whisper for detection, then Vistaar IndicWhisper for transcription
    - If model=whisper: Uses faster-whisper (best for all languages)
    """
    try:
        # Prefer multipart upload
        if audio is not None:
            audio_bytes = await audio.read()
            # Decide file suffix for temporary file based on incoming content type / filename
            incoming_suffix = None
            if audio.filename and '.' in audio.filename:
                incoming_suffix = '.' + audio.filename.split('.')[-1].lower()
            if not incoming_suffix:
                # Map common content-types to suffix
                ct = (audio.content_type or '').lower()
                if 'webm' in ct:
                    incoming_suffix = '.webm'
                elif 'ogg' in ct or 'opus' in ct:
                    incoming_suffix = '.ogg'
                elif 'wav' in ct:
                    incoming_suffix = '.wav'
                elif 'mp3' in ct:
                    incoming_suffix = '.mp3'
                elif 'm4a' in ct or 'mp4' in ct:
                    incoming_suffix = '.m4a'
                else:
                    incoming_suffix = '.webm'
            
            # Model selection: whisper (faster-whisper) or ai4bharat (vistaar-indicwhisper)
            model_choice = (model or "whisper").lower()
            
            if model_choice == "ai4bharat":
                # Use Vistaar IndicWhisper (best WER for Indian languages)
                # Fallback to faster-whisper if Vistaar is not available
                from ..services.faster_whisper_stt import get_faster_whisper_stt_service, FASTER_WHISPER_AVAILABLE
                
                detected_lang = lang
                detected_prob = None
                
                # Debug: Log received language parameter
                print(f"🔍 AI4Bharat STT - Received lang parameter: '{lang}'")
                
                # Normalize language code if provided (e.g., "hin_Deva" -> "hi", "hi" -> "hi")
                if detected_lang:
                    if "_" in detected_lang:
                        detected_lang = detected_lang.split("_")[0]
                    detected_lang = detected_lang[:2].lower()
                    print(f"🔍 AI4Bharat STT - Normalized to: '{detected_lang}'")
                
                # Try Vistaar IndicWhisper first
                try:
                    from ..services.vistaar_indicwhisper_stt import get_vistaar_indicwhisper_stt_service
                    
                    # Step 1: Detect language if not provided (using faster-whisper)
                    if not detected_lang:
                        if FASTER_WHISPER_AVAILABLE:
                            fw_service = get_faster_whisper_stt_service()
                            detect_result = await fw_service.transcribe(
                                audio_bytes,
                                language=None,
                                auto_detect_language=True,
                                model_size=None,
                                file_suffix=incoming_suffix,
                            )
                            detected_lang = detect_result.language
                            detected_prob = detect_result.language_probability
                            # Extract 2-letter code from BCP-47
                            if "_" in detected_lang:
                                detected_lang = detected_lang.split("_")[0]
                            detected_lang = detected_lang[:2]
                        else:
                            raise HTTPException(
                                status_code=400,
                                detail="Language detection requires faster-whisper. Please provide 'lang' parameter or install faster-whisper."
                            )
                    
                    # Step 2: Transcribe with Vistaar IndicWhisper
                    print(f"🎯 AI4Bharat STT - Loading model for language: '{detected_lang}'")
                    vistaar_service = get_vistaar_indicwhisper_stt_service()
                    result = await vistaar_service.transcribe(
                        audio_bytes,
                        language=detected_lang,
                        file_suffix=incoming_suffix,
                    )
                    return {
                        "text": result.text,
                        "language": result.language,
                        "language_probability": detected_prob,
                        "model": result.model,
                        "auto_detected": lang is None,
                        "segments": getattr(result, "segments", None),
                    }
                except (ImportError, RuntimeError, Exception) as e:
                    # Fallback to faster-whisper if Vistaar is not available
                    error_msg = str(e)
                    if "transformers" in error_msg or "Vistaar" in error_msg or "not available" in error_msg.lower():
                        print(f"⚠️  Vistaar IndicWhisper not available ({error_msg}), falling back to faster-whisper")
                        if not FASTER_WHISPER_AVAILABLE:
                            raise HTTPException(
                                status_code=500,
                                detail="Vistaar IndicWhisper is not available and faster-whisper is not installed. Please install faster-whisper: pip install faster-whisper ctranslate2"
                            )
                        # Use faster-whisper as fallback
                        fw_service = get_faster_whisper_stt_service()
                        result = await fw_service.transcribe(
                            audio_bytes,
                            language=detected_lang if detected_lang else None,
                            auto_detect_language=(not detected_lang),
                            model_size=None,
                            file_suffix=incoming_suffix,
                        )
                        return {
                            "text": result.text,
                            "language": result.language,
                            "language_probability": result.language_probability,
                            "model": f"faster-whisper-fallback-{result.model}",
                            "auto_detected": lang is None,
                            "segments": result.segments,
                        }
                    else:
                        raise
            else:
                # Use faster-whisper (supports 100+ languages), fallback to openai-whisper if needed
                from ..services.faster_whisper_stt import get_faster_whisper_stt_service, FASTER_WHISPER_AVAILABLE
                
                if FASTER_WHISPER_AVAILABLE:
                    try:
                        fw_service = get_faster_whisper_stt_service()
                        normalized_lang = None
                        if lang is not None and isinstance(lang, str) and lang.strip() != "":
                            normalized_lang = lang
                        result = await fw_service.transcribe(
                            audio_bytes,
                            language=normalized_lang,
                            auto_detect_language=(normalized_lang is None),
                            model_size=None,
                            file_suffix=incoming_suffix,
                            translate_to_english=translate_to_english,
                        )
                        return {
                            "text": result.text,
                            "language": result.language,
                            "language_probability": result.language_probability,
                            "model": result.model,
                            "auto_detected": normalized_lang is None,
                            "segments": result.segments,
                        }
                    except RuntimeError as e:
                        if "faster-whisper is not installed" in str(e):
                            print("⚠️  faster-whisper runtime error, falling back to openai-whisper")
                        else:
                            raise
                
                # Fallback to openai-whisper if faster-whisper is not available
                try:
                    import whisper
                    import tempfile
                    
                    # Cache whisper model to avoid reloading on every request
                    model_cache_key = "whisper_model_cache"
                    if model_cache_key not in globals():
                        model_name = os.getenv("WHISPER_MODEL", "base")
                        print(f"📥 Loading openai-whisper model '{model_name}' (first time, may take a moment)...")
                        globals()[model_cache_key] = whisper.load_model(model_name)
                        print(f"✅ openai-whisper model '{model_name}' loaded successfully")
                    
                    whisper_model = globals()[model_cache_key]
                    model_name = os.getenv("WHISPER_MODEL", "base")
                    
                    # Write audio to temp file
                    suffix = incoming_suffix or ".wav"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                        temp_file.write(audio_bytes)
                        temp_file_path = temp_file.name
                    
                    try:
                        # Transcribe
                        result = whisper_model.transcribe(
                            temp_file_path,
                            language=lang[:2] if lang and len(lang) >= 2 else None,
                            task="transcribe"
                        )
                        
                        # Get detected language
                        detected_lang = result.get("language", lang or "unknown")
                        detected_prob = None
                        
                        # Map to BCP-47
                        lang_map = {
                            'en': 'eng_Latn', 'hi': 'hin_Deva', 'bn': 'ben_Beng', 'ta': 'tam_Taml',
                            'te': 'tel_Telu', 'gu': 'guj_Gujr', 'kn': 'kan_Knda', 'ml': 'mal_Mlym',
                            'mr': 'mar_Deva', 'pa': 'pan_Guru', 'or': 'ory_Orya', 'as': 'asm_Beng',
                            'ur': 'urd_Arab', 'ne': 'nep_Deva', 'si': 'sin_Sinh',
                        }
                        bcp47_lang = lang_map.get(detected_lang, f"{detected_lang}_Latn")
                        
                        return {
                            "text": result["text"].strip(),
                            "language": bcp47_lang,
                            "language_probability": detected_prob,
                            "model": f"openai-whisper-{model_name}",
                            "auto_detected": lang is None,
                        }
                    finally:
                        if os.path.exists(temp_file_path):
                            try:
                                os.unlink(temp_file_path)
                            except Exception:
                                pass
                except ImportError:
                    raise HTTPException(
                        status_code=500,
                        detail="Neither faster-whisper nor openai-whisper is installed. Please install one: pip install faster-whisper ctranslate2 OR pip install openai-whisper"
                    )
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Whisper transcription failed: {str(e)}")

        # ULCA-style JSON body support
        if body and isinstance(body, dict) and "config" in body and "audio" in body:
            try:
                cfg = body.get("config", {}) or {}
                lang_cfg = (cfg.get("language") or {})
                source_lang = (lang_cfg.get("sourceLanguage") or None)
                if source_lang:
                    # Normalize e.g., eng_Latn -> eng -> en, or just use two-letter when provided
                    if "_" in source_lang:
                        source_lang = source_lang.split("_")[0]
                    source_lang = source_lang[:2]
                # Determine audio bytes: support audioContent (base64) or audioUri (http)
                audio_items = body.get("audio") or []
                if not audio_items:
                    raise HTTPException(status_code=400, detail="No audio items provided")
                item = audio_items[0]
                audio_bytes: Optional[bytes] = None
                incoming_suffix = None
                if "audioContent" in item and item["audioContent"]:
                    try:
                        audio_bytes = base64.b64decode(item["audioContent"], validate=True)
                    except Exception:
                        # Try forgiving decode
                        audio_bytes = base64.b64decode(item["audioContent"])
                    # Infer suffix from audioFormat
                    fmt = (cfg.get("audioFormat") or "").lower()
                    if fmt == "wav":
                        incoming_suffix = ".wav"
                    elif fmt == "mp3":
                        incoming_suffix = ".mp3"
                    elif fmt == "m4a":
                        incoming_suffix = ".m4a"
                    elif fmt == "ogg":
                        incoming_suffix = ".ogg"
                    elif fmt == "webm":
                        incoming_suffix = ".webm"
                elif "audioUri" in item and item["audioUri"]:
                    url = item["audioUri"]
                    async with httpx.AsyncClient(timeout=60) as client:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        audio_bytes = resp.content
                    # Infer suffix from URL
                    low = url.lower()
                    if low.endswith(".wav"):
                        incoming_suffix = ".wav"
                    elif low.endswith(".mp3"):
                        incoming_suffix = ".mp3"
                    elif low.endswith(".m4a") or low.endswith(".mp4"):
                        incoming_suffix = ".m4a"
                    elif low.endswith(".ogg") or low.endswith(".opus"):
                        incoming_suffix = ".ogg"
                    elif low.endswith(".webm"):
                        incoming_suffix = ".webm"
                else:
                    raise HTTPException(status_code=400, detail="Provide audioContent (base64) or audioUri")

                if not audio_bytes:
                    raise HTTPException(status_code=400, detail="Audio bytes are empty")

                # Use faster-whisper for transcription
                from ..services.faster_whisper_stt import get_faster_whisper_stt_service
                
                fw_service = get_faster_whisper_stt_service()
                result = await fw_service.transcribe(
                    audio_bytes,
                    language=source_lang,
                    auto_detect_language=(source_lang is None),
                    model_size=None,
                    file_suffix=incoming_suffix,
                )

                # ULCA-style response
                return {
                    "output": [{
                        "source": result.text
                    }],
                    "status": "SUCCESS"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        raise HTTPException(status_code=400, detail="Provide multipart form-data with 'audio' file")
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
            # Lazy import to avoid hard dependency at app startup
            from ..services.indictrans2 import get_indictrans2_service
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


