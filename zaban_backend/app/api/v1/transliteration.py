from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from ...services.ai4bharat import Ai4BharatClient
from ...core.api_key_auth import require_api_key


router = APIRouter(prefix="")


class TransliterateRequest(BaseModel):
    text: str
    source_script: str
    target_script: str
    lang: str
    topk: Optional[int] = 1


client = Ai4BharatClient()


@router.post("/transliterate")
async def transliterate(req: TransliterateRequest, _api_key=Depends(require_api_key)):
    try:
        return await client.transliterate(
            text=req.text,
            source_script=req.source_script,
            target_script=req.target_script,
            lang=req.lang,
            topk=req.topk,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


