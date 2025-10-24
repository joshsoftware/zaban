import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.main import app
from app.db.database import SessionLocal
from app.core.api_key_auth import generate_api_key
from app.models.api_key import ApiKey
from app.models.user import User


def _seed_user_and_key(db: Session, email: str = "tester@example.com", key_name: str = "test-key"):
    """Helper to create user and API key for testing"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    raw, key_hash = generate_api_key()
    key = ApiKey(user_id=user.id, name=key_name, key_hash=key_hash, is_active=True)
    db.add(key)
    db.commit()
    db.refresh(key)
    return user, key, raw


def _get_auth_headers(token: str) -> dict:
    """Helper to create authorization headers"""
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
@patch('app.api.v1.api_keys.verify_token')
async def test_create_api_key_success(mock_verify_token):
    """Test successful API key creation"""
    # Mock JWT verification to return a test email
    mock_verify_token.return_value = "test@example.com"
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create API key
        response = await ac.post(
            "/api/v1/api-keys",
            json={"name": "My Test Key"},
            headers=_get_auth_headers("test-jwt-token")
        )
        
        # Should return 200 with API key details
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "secret_key" in data
        assert data["name"] == "My Test Key"
        assert len(data["secret_key"]) > 0  # Raw key should be returned
        assert data["secret_key"].startswith("sk-")  # Should start with sk-


@pytest.mark.asyncio
@patch('app.api.v1.api_keys.verify_token')
async def test_create_api_key_without_name(mock_verify_token):
    """Test API key creation without name"""
    mock_verify_token.return_value = "test2@example.com"
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/api-keys",
            json={},
            headers=_get_auth_headers("test-jwt-token")
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] is None
        assert "secret_key" in data
        assert data["secret_key"].startswith("sk-")  # Should start with sk-


@pytest.mark.asyncio
async def test_create_api_key_without_auth():
    """Test API key creation without authentication"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/api-keys",
            json={"name": "Test Key"}
        )
        
        assert response.status_code == 401


@pytest.mark.asyncio
@patch('app.api.v1.api_keys.verify_token')
async def test_list_api_keys(mock_verify_token):
    """Test listing API keys for a user"""
    mock_verify_token.return_value = "list@example.com"
    
    # Seed user and keys directly in DB for test
    db = SessionLocal()
    try:
        user, key1, _ = _seed_user_and_key(db, "list@example.com", "Key 1")
        _, key2, _ = _seed_user_and_key(db, "list@example.com", "Key 2")
    finally:
        db.close()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/api-keys",
            headers=_get_auth_headers("test-jwt-token")
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "api_keys" in data
        assert "total" in data
        assert data["total"] == 2
        
        # Check that API keys are returned (without raw keys)
        api_keys = data["api_keys"]
        assert len(api_keys) == 2
        
        # Verify structure of each API key
        for key in api_keys:
            assert "id" in key
            assert "name" in key
            assert "is_active" in key
            assert "created_at" in key
            assert "secret_key" not in key  # Raw key should not be in list


@pytest.mark.asyncio
@patch('app.api.v1.api_keys.verify_token')
async def test_get_specific_api_key(mock_verify_token):
    """Test getting details of a specific API key"""
    mock_verify_token.return_value = "get@example.com"
    
    # Seed user and key directly in DB for test
    db = SessionLocal()
    try:
        user, key, _ = _seed_user_and_key(db, "get@example.com", "Specific Key")
    finally:
        db.close()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            f"/api/v1/api-keys/{key.id}",
            headers=_get_auth_headers("test-jwt-token")
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(key.id)
        assert data["name"] == "Specific Key"
        assert data["is_active"] is True
        assert "created_at" in data
        assert data["revoked_at"] is None
        assert "secret_key" not in data  # Raw key should not be returned


@pytest.mark.asyncio
@patch('app.api.v1.api_keys.verify_token')
async def test_get_nonexistent_api_key(mock_verify_token):
    """Test getting a non-existent API key"""
    mock_verify_token.return_value = "test@example.com"
    
    fake_id = str(uuid.uuid4())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            f"/api/v1/api-keys/{fake_id}",
            headers=_get_auth_headers("test-jwt-token")
        )
        
        assert response.status_code == 404


@pytest.mark.asyncio
@patch('app.api.v1.api_keys.verify_token')
async def test_delete_api_key(mock_verify_token):
    """Test deleting (deactivating) an API key"""
    mock_verify_token.return_value = "delete@example.com"
    
    # Seed user and key directly in DB for test
    db = SessionLocal()
    try:
        user, key, _ = _seed_user_and_key(db, "delete@example.com", "To Delete")
    finally:
        db.close()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Delete the API key
        response = await ac.delete(
            f"/api/v1/api-keys/{key.id}",
            headers=_get_auth_headers("test-jwt-token")
        )
        
        assert response.status_code == 204
        
        # Verify the key is deactivated
        response = await ac.get(
            f"/api/v1/api-keys/{key.id}",
            headers=_get_auth_headers("test-jwt-token")
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False


@pytest.mark.asyncio
@patch('app.api.v1.api_keys.verify_token')
async def test_delete_nonexistent_api_key(mock_verify_token):
    """Test deleting a non-existent API key"""
    mock_verify_token.return_value = "test@example.com"
    
    fake_id = str(uuid.uuid4())
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete(
            f"/api/v1/api-keys/{fake_id}",
            headers=_get_auth_headers("test-jwt-token")
        )
        
        assert response.status_code == 404


@pytest.mark.asyncio
@patch('app.api.v1.api_keys.verify_token')
async def test_api_key_usage_after_deletion(mock_verify_token):
    """Test that deleted API keys cannot be used for service access"""
    mock_verify_token.return_value = "usage@example.com"
    
    # Seed user and key directly in DB for test
    db = SessionLocal()
    try:
        user, key, raw_key = _seed_user_and_key(db, "usage@example.com", "Usage Test")
    finally:
        db.close()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First, verify the key works
        response = await ac.post(
            "/api/v1/translate",
            json={"text": "Hello", "source_lang": "eng_Latn", "target_lang": "hin_Deva"},
            headers={"X-API-Key": raw_key}
        )
        # Should work (may be 200 or 400 depending on model availability)
        assert response.status_code in (200, 400)
        
        # Now delete the key
        delete_response = await ac.delete(
            f"/api/v1/api-keys/{key.id}",
            headers=_get_auth_headers("test-jwt-token")
        )
        assert delete_response.status_code == 204
        
        # Try to use the deleted key again
        response = await ac.post(
            "/api/v1/translate",
            json={"text": "Hello", "source_lang": "eng_Latn", "target_lang": "hin_Deva"},
            headers={"X-API-Key": raw_key}
        )
        # Should now return 401 (unauthorized)
        assert response.status_code == 401


@pytest.mark.asyncio
@patch('app.api.v1.api_keys.verify_token')
async def test_user_isolation(mock_verify_token):
    """Test that users can only see their own API keys"""
    mock_verify_token.return_value = "user1@example.com"
    
    # Create keys for two different users
    db = SessionLocal()
    try:
        user1, key1, _ = _seed_user_and_key(db, "user1@example.com", "User 1 Key")
        user2, key2, _ = _seed_user_and_key(db, "user2@example.com", "User 2 Key")
    finally:
        db.close()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # User 1 should only see their own keys
        response = await ac.get(
            "/api/v1/api-keys",
            headers=_get_auth_headers("test-jwt-token")
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["api_keys"][0]["id"] == str(key1.id)
        
        # User 1 should not be able to access User 2's key
        response = await ac.get(
            f"/api/v1/api-keys/{key2.id}",
            headers=_get_auth_headers("test-jwt-token")
        )
        assert response.status_code == 404


@pytest.mark.asyncio
@patch('app.api.v1.api_keys.verify_token')
async def test_api_key_creation_creates_user(mock_verify_token):
    """Test that creating an API key automatically creates a user if they don't exist"""
    mock_verify_token.return_value = "newuser@example.com"
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create API key for non-existent user
        response = await ac.post(
            "/api/v1/api-keys",
            json={"name": "Auto User Key"},
            headers=_get_auth_headers("test-jwt-token")
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Auto User Key"
        assert "secret_key" in data
        assert data["secret_key"].startswith("sk-")  # Should start with sk-
        
        # Verify user was created and key is listed
        response = await ac.get(
            "/api/v1/api-keys",
            headers=_get_auth_headers("test-jwt-token")
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["api_keys"][0]["name"] == "Auto User Key"
