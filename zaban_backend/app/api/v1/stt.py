from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from typing import Optional

from ...services.ai4bharat import Ai4BharatClient


router = APIRouter(prefix="")


client = Ai4BharatClient()


@router.post("/stt")
async def stt(
    audio: Optional[UploadFile] = File(None),
    lang: Optional[str] = Form(None),
    format: Optional[str] = Form(None),
    body: Optional[dict] = Body(None),
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


