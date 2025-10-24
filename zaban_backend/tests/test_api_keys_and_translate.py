import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import SessionLocal
from app.core.api_key_auth import generate_api_key
from app.models.api_key import ApiKey
from app.models.user import User


def _seed_user_and_key(db: Session, email: str = "tester@example.com"):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    raw, key_hash = generate_api_key()
    key = ApiKey(user_id=user.id, name="test", key_hash=key_hash, is_active=True)
    db.add(key)
    db.commit()
    db.refresh(key)
    return user, key, raw


@pytest.mark.asyncio
async def test_translate_requires_api_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {"text": "Hello", "source_lang": "eng_Latn", "target_lang": "hin_Deva"}
        # No API key header -> 401
        r = await ac.post("/api/v1/translate", json=payload)
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_translate_with_invalid_api_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {"text": "Hello", "source_lang": "eng_Latn", "target_lang": "hin_Deva"}
        r = await ac.post("/api/v1/translate", json=payload, headers={"X-API-Key": "invalid"})
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_api_key_create_delete_and_use():
    # Seed user and key directly via DB for test
    db = SessionLocal()
    try:
        user, key, raw = _seed_user_and_key(db)
    finally:
        db.close()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {"text": "Hello", "source_lang": "eng_Latn", "target_lang": "hin_Deva"}
        # With valid API key header (no JWT in tests for simplicity)
        r = await ac.post("/api/v1/translate", json=payload, headers={"X-API-Key": raw})
        # May be 200 (if model is ready) or 400 (model unavailable); but not 401
        assert r.status_code in (200, 400)

        # Now delete key through DB and try again (simulate immediate revoke)
        db2 = SessionLocal()
        try:
            rec = db2.query(ApiKey).filter(ApiKey.id == key.id).first()
            rec.is_active = False
            db2.add(rec)
            db2.commit()
        finally:
            db2.close()

        r2 = await ac.post("/api/v1/translate", json=payload, headers={"X-API-Key": raw})
        assert r2.status_code == 401



