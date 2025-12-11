from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from typing import Optional

from ...services.ai4bharat import Ai4BharatClient


router = APIRouter(prefix="")


client = Ai4BharatClient()


@router.post("/stt")
async def stt(
    audio: Optional[UploadFile] = File(None),
    lang: Optional[str] = Form(None),
    model: Optional[str] = Form("whisper"),
    format: Optional[str] = Form(None),
    body: Optional[dict] = Body(None),
):
    try:
        if audio is not None:
            # For both Whisper and AI4Bharat models, delegate to routes/v1.py
            # routes/v1.py handles:
            # - Whisper: uses faster-whisper (lang optional, auto-detects)
            # - AI4Bharat: uses Vistaar IndicWhisper (lang required or auto-detects)
            model_choice = (model or "whisper").lower()
            
            # Delegate to routes/v1.py which handles both models correctly
            from ...routes.v1 import stt as stt_route
            return await stt_route(audio=audio, lang=lang, model=model, format=format, body=body)
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


