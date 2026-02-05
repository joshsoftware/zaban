import io

import httpx
from fastapi import APIRouter, HTTPException, Request
from starlette.datastructures import UploadFile

from ...services.ai4bharat import Ai4BharatClient


router = APIRouter(prefix="")


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


@router.post("/stt")
async def stt(request: Request):
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
                return {
                    "text": stt_result["text"],
                    "language": stt_result.get("language"),
                    "language_probability": stt_result.get("language_probability"),
                    "model": stt_result.get("model"),
                    "auto_detected": stt_result.get("auto_detected", False),
                    "translated_text": stt_result["text"],
                    "target_lang": "eng_Latn",
                    "translation_model": "faster-whisper-translate",
                    "segments": stt_result.get("segments"),
                }
            return stt_result

        # Multipart: parse form once (audio file + optional lang, model, format, translate_to_english)
        form = await request.form()
        audio = form.get("audio")
        if audio is None or not (hasattr(audio, "read") and hasattr(audio, "filename")):
            raise HTTPException(status_code=400, detail="Provide multipart with audio or JSON with audio_url")
        lang = form.get("lang") or None
        model = form.get("model") or "whisper"
        format_param = form.get("format") or None
        translate_to_english_form = _parse_bool(form.get("translate_to_english"))

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
            return {
                "text": stt_result["text"],
                "language": stt_result.get("language"),
                "language_probability": stt_result.get("language_probability"),
                "model": stt_result.get("model"),
                "auto_detected": stt_result.get("auto_detected", False),
                "translated_text": stt_result["text"],
                "target_lang": "eng_Latn",
                "translation_model": "faster-whisper-translate",
                "segments": stt_result.get("segments"),
            }
        return stt_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


