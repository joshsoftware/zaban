
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = "/home/josh/JOSH/LingoAI/Zaban/zaban-backend-v1/zaban_backend"
if project_root not in sys.path:
    sys.path.append(project_root)

print(f"Project root: {project_root}")
print(f"Python path: {sys.path}")

# Monkey patch torchaudio.list_audio_backends for compatibility with speechbrain
try:
    import torchaudio
    if not hasattr(torchaudio, "list_audio_backends"):
        print("Patching torchaudio.list_audio_backends for compatibility...")
        try:
            from torchaudio.utils import get_audio_backend_module
            torchaudio.list_audio_backends = lambda: [get_audio_backend_module()]
        except ImportError:
            torchaudio.list_audio_backends = lambda: ["ffmpeg"]
except ImportError:
    pass

try:
    from app.services.voiceprint.config import voiceprint_settings
    print(f"Voiceprint settings: {voiceprint_settings}")
    
    if voiceprint_settings.VOICEPRINT_ENABLED:
        from app.services.voiceprint.verifier import VoiceVerifierECAPA
        print("🚀 Attempting to initialize voiceprint verifier...")
        verifier = VoiceVerifierECAPA()
        print("Voiceprint verifier initialized SUCCESSFULLY.")
    else:
        print("Voiceprint service disabled (VOICEPRINT_ENABLED=false)")
except Exception as e:
    import traceback
    print(f"Voiceprint verifier initialization FAILED: {e}")
    traceback.print_exc()
