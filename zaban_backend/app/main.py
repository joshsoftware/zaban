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

# Monkey patch torchaudio.list_audio_backends for compatibility with speechbrain
# This is needed because some versions of speechbrain call this removed method
try:
    import torchaudio
    if not hasattr(torchaudio, "list_audio_backends"):
        print("ℹ️  Patching torchaudio.list_audio_backends for compatibility...")
        try:
            # For torchaudio >= 2.1
            from torchaudio.utils import get_audio_backend_module
            torchaudio.list_audio_backends = lambda: [get_audio_backend_module()]
        except ImportError:
            # Fallback
            torchaudio.list_audio_backends = lambda: ["ffmpeg"]
except ImportError:
    pass


app = FastAPI(title="AI4Bharat FastAPI Backend", version="0.1.0")

"""CORS configuration for browser-based clients (e.g., HTML tester).
- allow_origins: set to '*' for simplicity during development
- allow_credentials: keep False when using '*' (per CORS spec)
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://frontend:3000",  # Docker container name
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
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
            print(f"🚀 Preloading openai-whisper model '{model_name}' at startup...")
            service = get_faster_whisper_stt_service()
            service.load_model(model_name)
            print(f"✅ openai-whisper preloaded. Ready for all languages.")
        else:
            print("ℹ️  openai-whisper preload disabled (PRELOAD_WHISPER=false)")
    except Exception as e:
        print(f"⚠️  openai-whisper preload failed: {e}")
        print("   Model will be loaded on first request (slower)")

    # Initialize voiceprint verifier
    from .services.voiceprint.config import voiceprint_settings
    if voiceprint_settings.VOICEPRINT_ENABLED:
        try:
            from .services.voiceprint.verifier import VoiceVerifierECAPA
            print("🚀 Initializing voiceprint verifier...")
            app.state.voice_verifier = VoiceVerifierECAPA()
            print("✅ Voiceprint verifier initialized.")
        except Exception as e:
            print(f"⚠️  Voiceprint verifier initialization failed: {e}")
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


