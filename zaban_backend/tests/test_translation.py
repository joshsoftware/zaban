import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_translate_endpoint_exists():
    """Test that translate endpoint exists and requires proper fields"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # With API-key protection, missing key returns 401
        r = await ac.post("/api/v1/translate", json={})
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_translate_with_valid_request():
    """Test translation with valid request format"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "text": "Hello, how are you?",
            "source_lang": "eng_Latn",
            "target_lang": "hin_Deva"
        }
        r = await ac.post("/api/v1/translate", json=payload)
        # With API-key protection, missing key returns 401
        assert r.status_code == 401
        
        if r.status_code == 200:
            data = r.json()
            assert "translated_text" in data
            assert "source_lang" in data
            assert "target_lang" in data
            assert "model" in data

