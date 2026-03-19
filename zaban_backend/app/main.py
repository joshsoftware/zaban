from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
import asyncio
from pathlib import Path

# Import model manager for background cleanup
from .core.model_manager import model_manager

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
    """
    Actions to perform on application startup.
    Now uses 'Pure Lazy Loading' - no models are loaded on startup.
    Starts a background task for automatic model unloading if enabled.
    """
    load_dotenv(override=True)
    print("🚀 Starting Zaban Backend...")
    
    # Get model management configurations
    enable_auto_unload = os.getenv("ENABLE_AUTO_UNLOAD", "true").lower() == "true"
    idle_ttl = int(os.getenv("MODEL_IDLE_TTL", "300"))

    if enable_auto_unload:
        # Start the background cleanup task
        # This will periodically check for idle models and unload them from GPU memory.
        asyncio.create_task(model_manager.cleanup_loop(ttl_seconds=idle_ttl))
        print(f"⏱️ Model auto-unload enabled (TTL: {idle_ttl}s)")
    else:
        print("⚠️ Model auto-unload is disabled. Models will stay in memory once loaded.")

    # Initialize voiceprint verifier (Now lightweight, models load lazily)
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


