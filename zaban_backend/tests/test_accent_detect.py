import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_accent_detect_endpoint():
    # Patch FastAPI dependency to use DummyService
    from app.api.v1 import accent_detect
    class DummyService:
        async def detect_accent(self, audio_file):
            return {
                "accent": "hindi_north",
                "confidence": 0.95,
                "details": {"probs": {"hindi_north": 0.95, "hindi_south": 0.05}}
            }
    import app.main
    app.main.app.dependency_overrides[accent_detect.get_accent_detection_service] = lambda: DummyService()

    # Simulate a small wav file upload
    audio_bytes = b"RIFF....WAVEfmt "  # Not a real wav, just for test
    files = {"audio": ("test.wav", io.BytesIO(audio_bytes), "audio/wav")}
    response = client.post("/api/v1/accent-detect", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["accent"] == "hindi_north"
    assert 0.9 < data["confidence"] <= 1.0
    assert "details" in data
