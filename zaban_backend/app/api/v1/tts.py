from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ...services.ai4bharat import Ai4BharatClient


router = APIRouter(prefix="")


class TtsRequest(BaseModel):
    text: str
    lang: str
    speaker: Optional[str] = None
    sample_rate: Optional[int] = None
    format: Optional[str] = "wav"


client = Ai4BharatClient()


@router.post("/tts")
async def tts(req: TtsRequest):
    try:
        return await client.tts(
            text=req.text,
            lang=req.lang,
            speaker=req.speaker,
            sample_rate=req.sample_rate,
            fmt=req.format,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


