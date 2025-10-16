from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi import Body
from pydantic import BaseModel
from typing import Optional, List

from ..services.ai4bharat import Ai4BharatClient


router = APIRouter()


class TtsRequest(BaseModel):
    text: str
    lang: str
    speaker: Optional[str] = None
    sample_rate: Optional[int] = None
    format: Optional[str] = "wav"


class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str
    domain: Optional[str] = None


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
    try:
        return await client.translate(text=req.text, source_lang=req.source_lang, target_lang=req.target_lang, domain=req.domain)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transliterate")
async def transliterate(req: TransliterateRequest):
    try:
        return await client.transliterate(text=req.text, source_script=req.source_script, target_script=req.target_script, lang=req.lang, topk=req.topk)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


