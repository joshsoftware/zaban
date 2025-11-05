from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .routes.v1 import router as v1_router
from .routes import auth as auth_routes
import os


app = FastAPI(title="AI4Bharat FastAPI Backend", version="0.1.0")

"""CORS configuration for browser-based clients (e.g., HTML tester).
- allow_origins: set to '*' for simplicity during development
- allow_credentials: keep False when using '*' (per CORS spec)
"""
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
    
    # Preload faster-whisper model once at startup to avoid per-request loads
    try:
        if os.getenv("PRELOAD_FASTER_WHISPER", "true").lower() == "true":
            from .services.faster_whisper_stt import get_faster_whisper_stt_service
            model_name = os.getenv("WHISPER_MODEL", "large-v3")
            print(f"🚀 Preloading faster-whisper model '{model_name}' at startup...")
            service = get_faster_whisper_stt_service()
            service.load_model(model_name)
            print(f"✅ faster-whisper model '{model_name}' preloaded successfully. Ready for all languages.")
        else:
            print("ℹ️  faster-whisper preload disabled (PRELOAD_FASTER_WHISPER=false)")
    except Exception as e:
        print(f"⚠️  faster-whisper preload failed: {e}")
        print("   Model will be loaded on first request (slower)")


@app.get("/up")
async def up():
    return {"status": "ok"}


app.include_router(v1_router, prefix="/api/v1")
app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["auth"])


