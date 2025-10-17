from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

from ...services.ai4bharat import Ai4BharatClient
from ...services.indictrans2 import get_indictrans2_service


router = APIRouter(prefix="")


class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str
    domain: Optional[str] = None


client = Ai4BharatClient()


@router.post("/translate")
async def translate(req: TranslateRequest):
    """
    Translate text using IndicTrans2 model (local) or external API.
    """
    try:
        use_local = os.getenv("USE_LOCAL_INDICTRANS2", "true").lower() == "true"
        if use_local:
            indictrans_service = get_indictrans2_service()
            translated_text = await indictrans_service.translate(
                text=req.text,
                source_lang=req.source_lang,
                target_lang=req.target_lang
            )
            return {
                "translated_text": translated_text,
                "source_lang": req.source_lang,
                "target_lang": req.target_lang,
                "model": "indictrans2-local"
            }
        else:
            result = await client.translate(
                text=req.text,
                source_lang=req.source_lang,
                target_lang=req.target_lang,
                domain=req.domain
            )
            if isinstance(result, dict):
                result["model"] = "external-api"
            return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


