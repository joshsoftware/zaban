from fastapi import APIRouter

from .translation import router as translation_router
from .tts import router as tts_router
from .stt import router as stt_router
from .transliteration import router as transliteration_router


router = APIRouter()

router.include_router(translation_router)
router.include_router(tts_router)
router.include_router(stt_router)
router.include_router(transliteration_router)


