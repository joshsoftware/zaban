#!/usr/bin/env python
"""
Test translation endpoint with auto-detection
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

from app.main import app
from app.models.api_key import ApiKey
from app.models.user import User
import uuid
from datetime import datetime

client = TestClient(app)


def _get_auth_headers(api_key: str) -> dict:
    return {"X-API-Key": api_key}


@pytest.fixture
def mock_api_key():
    """Create a mock API key for testing"""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    api_key = ApiKey(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Test API Key",
        key_hash="hashed_key",
        is_active=True,
        created_at=datetime.utcnow(),
        revoked_at=None
    )
    
    return api_key


@pytest.mark.asyncio
@patch('app.services.indictrans2.IndicTrans2Service.translate')
async def test_translation_auto_detect_hindi(mock_translate, mock_api_key):
    """Test translation with auto-detection of Hindi"""
    mock_translate.return_value = "Hello world"
    
    with patch('app.core.api_key_auth.verify_api_key') as mock_verify:
        mock_verify.return_value = mock_api_key
        
        response = client.post(
            "/api/v1/translate",
            headers=_get_auth_headers("sk-test-api-key"),
            json={
                "text": "नमस्ते दुनिया",
                "target_lang": "eng_Latn",
                "auto_detect": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["translated_text"] == "Hello world"
        assert data["source_lang"] == "hin_Deva"  # Auto-detected
        assert data["target_lang"] == "eng_Latn"
        assert data["auto_detected"] is True
        
        # Verify the service was called with detected language
        mock_translate.assert_called_once_with(
            text="नमस्ते दुनिया",
            source_lang="hin_Deva",
            target_lang="eng_Latn"
        )


@pytest.mark.asyncio
@patch('app.services.indictrans2.IndicTrans2Service.translate')
async def test_translation_auto_detect_english(mock_translate, mock_api_key):
    """Test translation with auto-detection of English"""
    mock_translate.return_value = "नमस्ते दुनिया"
    
    with patch('app.core.api_key_auth.verify_api_key') as mock_verify:
        mock_verify.return_value = mock_api_key
        
        response = client.post(
            "/api/v1/translate",
            headers=_get_auth_headers("sk-test-api-key"),
            json={
                "text": "Hello world",
                "target_lang": "hin_Deva",
                "auto_detect": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["translated_text"] == "नमस्ते दुनिया"
        assert data["source_lang"] == "eng_Latn"  # Auto-detected
        assert data["target_lang"] == "hin_Deva"
        assert data["auto_detected"] is True


@pytest.mark.asyncio
@patch('app.services.indictrans2.IndicTrans2Service.translate')
async def test_translation_auto_detect_tamil(mock_translate, mock_api_key):
    """Test translation with auto-detection of Tamil"""
    mock_translate.return_value = "Hello world"
    
    with patch('app.core.api_key_auth.verify_api_key') as mock_verify:
        mock_verify.return_value = mock_api_key
        
        response = client.post(
            "/api/v1/translate",
            headers=_get_auth_headers("sk-test-api-key"),
            json={
                "text": "வணக்கம் உலகம்",
                "target_lang": "eng_Latn",
                "auto_detect": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["translated_text"] == "Hello world"
        assert data["source_lang"] == "tam_Taml"  # Auto-detected
        assert data["target_lang"] == "eng_Latn"
        assert data["auto_detected"] is True


@pytest.mark.asyncio
@patch('app.services.indictrans2.IndicTrans2Service.translate')
async def test_translation_without_auto_detect(mock_translate, mock_api_key):
    """Test translation without auto-detection (explicit source_lang)"""
    mock_translate.return_value = "Hello world"
    
    with patch('app.core.api_key_auth.verify_api_key') as mock_verify:
        mock_verify.return_value = mock_api_key
        
        response = client.post(
            "/api/v1/translate",
            headers=_get_auth_headers("sk-test-api-key"),
            json={
                "text": "नमस्ते दुनिया",
                "source_lang": "hin_Deva",
                "target_lang": "eng_Latn"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["translated_text"] == "Hello world"
        assert data["source_lang"] == "hin_Deva"  # Explicitly provided
        assert data["target_lang"] == "eng_Latn"
        assert data["auto_detected"] is False


@pytest.mark.asyncio
@patch('app.services.indictrans2.IndicTrans2Service.translate')
async def test_translation_auto_detect_missing_source_lang(mock_translate, mock_api_key):
    """Test translation with auto-detection when source_lang is not provided"""
    mock_translate.return_value = "Hello world"
    
    with patch('app.core.api_key_auth.verify_api_key') as mock_verify:
        mock_verify.return_value = mock_api_key
        
        response = client.post(
            "/api/v1/translate",
            headers=_get_auth_headers("sk-test-api-key"),
            json={
                "text": "नमस्ते दुनिया",
                "target_lang": "eng_Latn"
                # No source_lang provided, should auto-detect
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["translated_text"] == "Hello world"
        assert data["source_lang"] == "hin_Deva"  # Auto-detected
        assert data["target_lang"] == "eng_Latn"
        assert data["auto_detected"] is True


@pytest.mark.asyncio
async def test_translation_auto_detect_validation_errors(mock_api_key):
    """Test validation errors for auto-detection"""
    with patch('app.core.api_key_auth.verify_api_key') as mock_verify:
        mock_verify.return_value = mock_api_key
        
        # Missing text
        response = client.post(
            "/api/v1/translate",
            headers=_get_auth_headers("sk-test-api-key"),
            json={
                "target_lang": "eng_Latn",
                "auto_detect": True
            }
        )
        assert response.status_code == 422
        
        # Missing target_lang
        response = client.post(
            "/api/v1/translate",
            headers=_get_auth_headers("sk-test-api-key"),
            json={
                "text": "नमस्ते दुनिया",
                "auto_detect": True
            }
        )
        assert response.status_code == 422


@pytest.mark.asyncio
@patch('app.services.indictrans2.IndicTrans2Service.translate')
async def test_translation_auto_detect_low_confidence(mock_translate, mock_api_key):
    """Test auto-detection with low confidence (should default to English)"""
    mock_translate.return_value = "Hello world"
    
    with patch('app.core.api_key_auth.verify_api_key') as mock_verify:
        mock_verify.return_value = mock_api_key
        
        # Test with ambiguous text that should default to English
        response = client.post(
            "/api/v1/translate",
            headers=_get_auth_headers("sk-test-api-key"),
            json={
                "text": "123456789",
                "target_lang": "hin_Deva",
                "auto_detect": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["translated_text"] == "Hello world"
        assert data["source_lang"] == "eng_Latn"  # Default fallback
        assert data["target_lang"] == "hin_Deva"
        assert data["auto_detected"] is True


@pytest.mark.asyncio
@patch('app.services.indictrans2.IndicTrans2Service.translate')
async def test_translation_auto_detect_multiple_languages(mock_translate, mock_api_key):
    """Test auto-detection with multiple Indian languages"""
    mock_translate.return_value = "Translated text"
    
    with patch('app.core.api_key_auth.verify_api_key') as mock_verify:
        mock_verify.return_value = mock_api_key
        
        test_cases = [
            ("नमस्ते", "hin_Deva"),  # Hindi
            ("হ্যালো", "ben_Beng"),  # Bengali
            ("வணக்கம்", "tam_Taml"),  # Tamil
            ("నమస్కారం", "tel_Telu"),  # Telugu
            ("નમસ્તે", "guj_Gujr"),  # Gujarati
        ]
        
        for text, expected_lang in test_cases:
            response = client.post(
                "/api/v1/translate",
                headers=_get_auth_headers("sk-test-api-key"),
                json={
                    "text": text,
                    "target_lang": "eng_Latn",
                    "auto_detect": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["source_lang"] == expected_lang
            assert data["auto_detected"] is True
