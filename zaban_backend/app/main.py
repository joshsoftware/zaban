from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables as early as possible so modules that read env at
# import time (e.g., OAuth clients) receive the correct values.
load_dotenv(override=True)

# Use the consolidated API v1 router that includes translation, TTS/STT,
# transliteration, and API key endpoints
from .api.v1 import router as v1_router
from .routes import auth as auth_routes



app = FastAPI(title="AI4Bharat FastAPI Backend", version="0.1.0")

# CORS – allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Load environment variables and preload models at startup."""
    load_dotenv(override=True)
    
    # Preload openai-whisper STT at startup
    try:
        if os.getenv("PRELOAD_WHISPER", "true").lower() == "true":
            from .services.faster_whisper_stt import get_faster_whisper_stt_service
            model_name = os.getenv("WHISPER_MODEL", "medium")
            service = get_faster_whisper_stt_service()
            service.load_model(model_name)
    except Exception as e:
        print(f"⚠️  openai-whisper preload failed: {e}")
        print("   Model will be loaded on first request (slower)")

    # Initialize voiceprint verifier
    from .services.voiceprint.config import voiceprint_settings
    if voiceprint_settings.VOICEPRINT_ENABLED:
        try:
            # Import at function level to catch import-time errors
            from .services.voiceprint.verifier import VoiceVerifierECAPA
            app.state.voice_verifier = VoiceVerifierECAPA()
            print("✅ Voiceprint verifier initialized.")
        except (TypeError, ImportError, AttributeError) as e:
            error_str = str(e)
            app.state.voice_verifier = None
        except Exception as e:
            import traceback
            print(f"⚠️  Voiceprint verifier initialization failed: {e}")
            print(f"Full traceback:")
            traceback.print_exc()
            app.state.voice_verifier = None
    else:
        print("ℹ️  Voiceprint service disabled (VOICEPRINT_ENABLED=false)")


@app.get("/up")
async def up():
    return {"status": "ok"}


@app.get("/translate-ui")
async def translation_ui():
    """Serve the translation UI HTML page"""
    docs_dir = Path(__file__).parent.parent / "docs"
    html_file = docs_dir / "test_translation.html"
    if html_file.exists():
        return FileResponse(html_file, media_type="text/html")
    return {"error": "Translation UI not found"}


@app.get("/stt-ui")
async def stt_ui():
    """Serve the STT UI HTML page"""
    docs_dir = Path(__file__).parent.parent / "docs"
    html_file = docs_dir / "test_stt_voice.html"
    if html_file.exists():
        return FileResponse(html_file, media_type="text/html")
    return {"error": "STT UI not found"}


app.include_router(v1_router, prefix="/api/v1")
app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["auth"])


