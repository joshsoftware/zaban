import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_me_requires_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_logout_requires_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/logout")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_google_login_not_configured(monkeypatch):
    # Without proper Google env and mocking, calling the endpoint should propagate an error (400/500)
    payload = {"code": "dummy", "redirect_uri": "http://localhost/callback"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/google/login", json=payload)
    assert r.status_code in (400, 500)


@pytest.mark.asyncio
async def test_domain_enforcement(monkeypatch):
    # Mock Google client methods to bypass external calls
    from app.services import google_oauth2

    async def fake_get_access_token(*args, **kwargs) -> str:
        return "fake-token"

    async def fake_get_user_info(access_token: str):
        return {"email": "user@notallowed.com"}

    monkeypatch.setattr(google_oauth2.google_oauth2_client, "get_access_token", fake_get_access_token)
    monkeypatch.setattr(google_oauth2.google_oauth2_client, "get_user_info", fake_get_user_info)

    os.environ["ALLOWED_SSO_DOMAINS"] = "joshsoftware.com"
    payload = {"code": "dummy", "redirect_uri": "http://localhost/callback"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/google/login", json=payload)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_successful_login_and_logout(monkeypatch):
    # Mock Google client for allowed domain
    from app.services import google_oauth2

    async def fake_get_access_token(*args, **kwargs) -> str:
        return "fake-token"

    async def fake_get_user_info(access_token: str):
        return {"email": "user@joshsoftware.com"}

    monkeypatch.setattr(google_oauth2.google_oauth2_client, "get_access_token", fake_get_access_token)
    monkeypatch.setattr(google_oauth2.google_oauth2_client, "get_user_info", fake_get_user_info)

    os.environ["ALLOWED_SSO_DOMAINS"] = "joshsoftware.com"
    payload = {"code": "dummy", "redirect_uri": "http://localhost/callback"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/google/login", json=payload)
        assert r.status_code == 200
        token = r.json()["access_token"]

        r_me = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r_me.status_code == 200

        r_logout = await ac.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert r_logout.status_code == 200

        # Token should be invalid after logout
        r_me2 = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r_me2.status_code == 401


