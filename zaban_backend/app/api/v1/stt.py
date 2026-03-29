import io
import logging

import httpx
from fastapi import APIRouter, HTTPException, Request, Depends
from starlette.datastructures import UploadFile

from ...services.ai4bharat import Ai4BharatClient
from ...core.api_key_auth import require_api_key


router = APIRouter(prefix="")
logger = logging.getLogger(__name__)


client = Ai4BharatClient()


def _filename_from_url(url: str) -> str:
    path = url.split("?")[0].rstrip("/")
    name = path.split("/")[-1] if "/" in path else "audio"
    return name if "." in name else "audio.webm"


def _parse_bool(val) -> bool:
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes")
    return bool(val)


def _log_stt_response(response: dict, request_kind: str) -> None:
    """Log a summary of the STT response for debugging."""
    text = response.get("text") or ""
    text_preview = (text[:120] + "…") if len(text) > 120 else text
    logger.info(
        "[STT response] kind=%s | language=%s | model=%s | text_len=%s | auto_detected=%s | keys=%s",
        request_kind,
        response.get("language"),
        response.get("model"),
        len(text),
        response.get("auto_detected"),
        list(response.keys()),
    )
    logger.info("[STT response] text_preview: %s", repr(text_preview))
    if response.get("translated_text") is not None:
        logger.info("[STT response] translate_to_english=true | target_lang=%s", response.get("target_lang"))


@router.post("/stt")
async def stt(request: Request, _api_key=Depends(require_api_key)):
    """
    Speech-to-Text: accept either multipart (audio file) or JSON (audio_url, optional lang).
    JSON: audio_url required; lang optional (auto-detect when omitted).
    Optional translate_to_english: if true, use Whisper translate (output in English).
    model: "whisper" (default, local) or "ai4bharat" (external; requires AI4B_* URL and lang).
    """
    try:
        content_type = (request.headers.get("content-type") or "").lower()

        if "application/json" in content_type:
            body = await request.json()
            if not body or not isinstance(body, dict):
                raise HTTPException(status_code=400, detail="Provide multipart with audio or JSON with audio_url")
            audio_url = body.get("audio_url")
            lang_json = body.get("lang") or None  # optional: None => auto-detect
            fmt_json = body.get("format")
            model_json = (body.get("model") or "whisper").lower().strip()
            translate_to_english = _parse_bool(body.get("translate_to_english"))
            logger.info(
                "[STT request] JSON | audio_url=%s | lang=%s | model=%s | format=%s | translate_to_english=%s",
                audio_url,
                lang_json,
                model_json,
                fmt_json,
                translate_to_english,
            )
            if not audio_url:
                raise HTTPException(status_code=400, detail="audio_url is required")

            if model_json == "ai4bharat":
                if not lang_json:
                    raise HTTPException(status_code=400, detail="lang is required when model is ai4bharat")
                return await client.stt_url(audio_url=audio_url, lang=lang_json, fmt=fmt_json)

            # model=whisper (default): fetch audio from URL and run through local Whisper pipeline
            async with httpx.AsyncClient(timeout=300) as http_client:
                resp = await http_client.get(audio_url)
                resp.raise_for_status()
                audio_bytes = resp.content
            filename = _filename_from_url(audio_url)
            upload_file = UploadFile(filename=filename, file=io.BytesIO(audio_bytes))
            from ...routes.v1 import stt as stt_route
            stt_result = await stt_route(
                audio=upload_file,
                lang=lang_json,
                model="whisper",
                format=fmt_json,
                body=None,
                translate_to_english=translate_to_english,
            )
            if translate_to_english:
                out = {
                    "text": stt_result["text"],
                    "language": stt_result.get("language"),
                    "language_probability": stt_result.get("language_probability"),
                    "model": stt_result.get("model"),
                    "auto_detected": stt_result.get("auto_detected", False),
                    "translated_text": stt_result["text"],
                    "target_lang": "eng_Latn",
                    "translation_model": "whisper-translate",
                    "segments": stt_result.get("segments"),
                }
                _log_stt_response(out, "json")
                return out
            _log_stt_response(stt_result, "json")
            return stt_result

        # Multipart: parse form once (audio file + optional lang, model, format, translate_to_english)
        form = await request.form()
        audio = form.get("audio")
        if audio is None or not (hasattr(audio, "read") and hasattr(audio, "filename")):
            raise HTTPException(status_code=400, detail="Provide multipart with audio or JSON with audio_url")
        # Accept both "lang" and "language" for source language (e.g. mr, hi, en)
        _lang = form.get("lang") or form.get("language") or None
        if isinstance(_lang, str):
            _lang = _lang.strip().strip('"').strip("'")
        lang = _lang if _lang else None
        model = form.get("model") or "whisper"
        format_param = form.get("format") or None
        translate_to_english_form = _parse_bool(form.get("translate_to_english"))
        audio_filename = getattr(audio, "filename", None)
        audio_size = None
        if hasattr(audio, "file") and hasattr(audio.file, "seek"):
            try:
                pos = audio.file.tell()
                audio.file.seek(0, 2)
                audio_size = audio.file.tell()
                audio.file.seek(pos)
            except Exception:
                pass
        logger.info(
            "[STT request] multipart | audio_file=%s | size=%s | lang=%s | model=%s | format=%s | translate_to_english=%s",
            audio_filename,
            audio_size,
            lang,
            model,
            format_param,
            translate_to_english_form,
        )

        from ...routes.v1 import stt as stt_route
        stt_result = await stt_route(
            audio=audio,
            lang=lang,
            model=model,
            format=format_param,
            body=None,
            translate_to_english=translate_to_english_form,
        )
        if translate_to_english_form:
            out = {
                "text": stt_result["text"],
                "language": stt_result.get("language"),
                "language_probability": stt_result.get("language_probability"),
                "model": stt_result.get("model"),
                "auto_detected": stt_result.get("auto_detected", False),
                "translated_text": stt_result["text"],
                "target_lang": "eng_Latn",
                "translation_model": "whisper-translate",
                "segments": stt_result.get("segments"),
            }
            _log_stt_response(out, "multipart")
            return out
        _log_stt_response(stt_result, "multipart")
        return stt_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


