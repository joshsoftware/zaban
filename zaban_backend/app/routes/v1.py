import os
import base64
import httpx
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi import Body
from pydantic import BaseModel

from ..services.ai4bharat import Ai4BharatClient
from ..services.indicwav2vec_stt import get_indicwav2vec_stt_service
from ..services.language_detection import get_language_detector


router = APIRouter()

# Optional faster-whisper detector cache
_fw_model = None


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
    """Speech-to-Text: Whisper auto-detect for language ONLY, Indic (Wav2Vec) for transcription.

    Behavior:
    - If `lang` provided: use it directly for IndicConformer
    - Else: standard Whisper language detection (single window, no priors)
    - Transcription: IndicConformer only (no Whisper fallback)
    """
    try:
        use_indicwav2vec = os.getenv("USE_INDICWAV2VEC", "false").lower() == "true"

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
            # IndicWav2Vec pipeline (no NeMo) - DISABLED, using Whisper
            if False:  # use_indicwav2vec disabled
                detected_lang = None
                detected_prob = None
                if lang:
                    detected_lang = lang.split('_')[0]
                else:
                    # Language detection
                    if os.getenv("USE_FASTER_WHISPER_DETECT", "false").lower() == "true":
                        # Use faster-whisper to avoid numba/llvmlite
                        try:
                            from faster_whisper import WhisperModel
                            fw = globals().get("_fw_model")
                            if fw is None:
                                model_name = os.getenv("WHISPER_MODEL", "large-v3")
                                fw = WhisperModel(
                                    model_name,
                                    device="cuda" if os.getenv("USE_CUDA", "false").lower()=="true" else "cpu",
                                )
                                globals()["_fw_model"] = fw
                            # Write temp file
                            import tempfile
                            suffix = incoming_suffix or '.wav'
                            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tf:
                                tf.write(audio_bytes)
                                tmp_path = tf.name
                            try:
                                segments, info = fw.transcribe(tmp_path, beam_size=1, vad_filter=False)
                                detected_lang = info.language
                                detected_prob = float(info.language_probability) if hasattr(info, 'language_probability') else None
                            finally:
                                try:
                                    os.unlink(tmp_path)
                                except Exception:
                                    pass
                        except Exception:
                            # Fallback: no detection
                            detected_lang = None
                            detected_prob = None
                    else:
                        # Use standard whisper service detection (may require numba)
                        from ..services.whisper_stt import get_whisper_stt_service
                        _ws = get_whisper_stt_service()
                        detected_lang, detected_prob = await _ws.detect_language_standard(audio_bytes, incoming_suffix)
                if not detected_lang:
                    raise HTTPException(status_code=400, detail="Language detection failed. Provide 'lang' explicitly.")

                indic_service = get_indicwav2vec_stt_service()
                indic_result = await indic_service.transcribe(audio_bytes, language=detected_lang)
                return {
                    "text": indic_result.text,
                    "language": detected_lang,
                    "language_probability": detected_prob,
                    "model": indic_result.model,
                    "auto_detected": lang is None,
                }
            else:
                # Use faster-whisper (no llvmlite dependency)
                from ..services.faster_whisper_stt import get_faster_whisper_stt_service
                fw_service = get_faster_whisper_stt_service()
                result = await fw_service.transcribe(
                    audio_bytes,
                    language=lang,
                    auto_detect_language=(lang is None),
                    model_size=None,
                    file_suffix=incoming_suffix,
                )
                return {
                    "text": result.text,
                    "language": result.language,
                    "language_probability": result.language_probability,
                    "model": result.model,
                    "auto_detected": lang is None,
                }

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

                # Use IndicWav2Vec flow (detection if source_lang missing)
                detected_lang = source_lang
                detected_prob = None
                if not detected_lang:
                    # Use faster-whisper if available
                    try:
                        from faster_whisper import WhisperModel
                        fw = globals().get("_fw_model")
                        if fw is None:
                            model_name = os.getenv("WHISPER_MODEL", "large-v3")
                            fw = WhisperModel(model_name, device="cuda" if os.getenv("USE_CUDA", "false").lower()=="true" else "cpu")
                            globals()["_fw_model"] = fw
                        # temp file for detection
                        import tempfile
                        suffix = incoming_suffix or ".wav"
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tf:
                            tf.write(audio_bytes)
                            tmp_path = tf.name
                        try:
                            segments, info = fw.transcribe(tmp_path, beam_size=1, vad_filter=False)
                            detected_lang = info.language
                            detected_prob = float(getattr(info, 'language_probability', 0.0))
                        finally:
                            try:
                                os.unlink(tmp_path)
                            except Exception:
                                pass
                    except Exception:
                        detected_lang = None

                if not detected_lang:
                    raise HTTPException(status_code=400, detail="Language detection failed. Provide config.language.sourceLanguage.")

                indic_service = get_indicwav2vec_stt_service()
                indic_result = await indic_service.transcribe(audio_bytes, language=detected_lang)

                # ULCA-style response
                return {
                    "output": [{
                        "source": indic_result.text
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


