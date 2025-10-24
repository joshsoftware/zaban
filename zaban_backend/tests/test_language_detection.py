#!/usr/bin/env python
"""
Test language detection functionality
"""
import pytest
from app.services.language_detection import get_language_detector, LanguageDetectionResult


def test_language_detection_basic():
    """Test basic language detection"""
    detector = get_language_detector()
    
    # Test Hindi detection
    result = detector.detect_language("नमस्ते दुनिया")
    assert result.detected_lang == "hin_Deva"
    assert result.confidence > 0.5
    assert result.is_auto_detected is True
    
    # Test English detection
    result = detector.detect_language("Hello world")
    assert result.detected_lang == "eng_Latn"
    assert result.confidence > 0.0
    assert result.is_auto_detected is True
    
    # Test Tamil detection
    result = detector.detect_language("வணக்கம்")
    assert result.detected_lang == "tam_Taml"
    assert result.confidence > 0.0
    assert result.is_auto_detected is True


def test_language_detection_confidence():
    """Test language detection confidence levels"""
    detector = get_language_detector()
    
    # High confidence - clear script
    result = detector.detect_language("नमस्ते दुनिया आप कैसे हैं")
    assert result.confidence > 0.7
    
    # Medium confidence - mixed content
    result = detector.detect_language("Hello नमस्ते")
    assert result.confidence > 0.0
    
    # Low confidence - ambiguous
    result = detector.detect_language("123")
    assert result.confidence >= 0.0


def test_language_detection_edge_cases():
    """Test edge cases for language detection"""
    detector = get_language_detector()
    
    # Empty text
    result = detector.detect_language("")
    assert result.detected_lang == "eng_Latn"
    assert result.confidence == 0.0
    
    # Whitespace only
    result = detector.detect_language("   \n\t   ")
    assert result.detected_lang == "eng_Latn"
    assert result.confidence == 0.0
    
    # Numbers only
    result = detector.detect_language("123456")
    assert result.detected_lang == "eng_Latn"  # Default fallback
    
    # Special characters
    result = detector.detect_language("!@#$%^&*()")
    assert result.detected_lang == "eng_Latn"  # Default fallback


def test_language_detection_multiple_languages():
    """Test detection with multiple Indian languages"""
    detector = get_language_detector()
    
    test_cases = [
        ("नमस्ते", "hin_Deva"),  # Hindi
        ("হ্যালো", "ben_Beng"),  # Bengali
        ("வணக்கம்", "tam_Taml"),  # Tamil
        ("నమస్కారం", "tel_Telu"),  # Telugu
        ("નમસ્તે", "guj_Gujr"),  # Gujarati
        ("ನಮಸ್ಕಾರ", "kan_Knda"),  # Kannada
        ("നമസ്കാരം", "mal_Mlym"),  # Malayalam
        ("ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "pan_Guru"),  # Punjabi
        ("ନମସ୍କାର", "ory_Orya"),  # Odia
    ]
    
    for text, expected_lang in test_cases:
        result = detector.detect_language(text)
        assert result.detected_lang == expected_lang, f"Failed for text: {text}"
        assert result.confidence > 0.0, f"Low confidence for text: {text}"
    
    # Test Devanagari script languages (Hindi, Marathi, Nepali, Sanskrit)
    # These share the same script, so we test that they're detected as Devanagari-based
    devanagari_texts = [
        ("नमस्ते", "hin_Deva"),  # Hindi
        ("नमस्कार", "mar_Deva"),  # Marathi (will be detected as Hindi due to script)
        ("नमस्कार", "npi_Deva"),  # Nepali (will be detected as Hindi due to script)
        ("नमस्ते", "san_Deva"),  # Sanskrit (will be detected as Hindi due to script)
    ]
    
    for text, expected_lang in devanagari_texts:
        result = detector.detect_language(text)
        # For Devanagari script, we expect it to be detected as one of the Devanagari languages
        assert result.detected_lang in ["hin_Deva", "mar_Deva", "npi_Deva", "san_Deva"], f"Failed for text: {text}, got: {result.detected_lang}"
        assert result.confidence > 0.0, f"Low confidence for text: {text}"


def test_language_detection_script_based():
    """Test script-based detection"""
    detector = get_language_detector()
    
    # Devanagari script (Hindi/Marathi/Nepali/Sanskrit)
    result = detector.detect_language("यह हिंदी है")
    assert result.detected_lang in ["hin_Deva", "mar_Deva", "npi_Deva", "san_Deva"]
    assert result.method == "script"
    
    # Bengali script
    result = detector.detect_language("এটি বাংলা")
    assert result.detected_lang in ["ben_Beng", "asm_Beng", "mni_Beng"]
    assert result.method == "script"
    
    # Tamil script
    result = detector.detect_language("இது தமிழ்")
    assert result.detected_lang == "tam_Taml"
    assert result.method == "script"


def test_language_detection_word_based():
    """Test word-based detection"""
    detector = get_language_detector()
    
    # Hindi with common words
    result = detector.detect_language("मैं आपसे मिलकर खुश हूं")
    assert result.detected_lang == "hin_Deva"
    assert result.method == "words"
    
    # English with common words
    result = detector.detect_language("I am happy to meet you")
    assert result.detected_lang == "eng_Latn"
    assert result.method == "words"


def test_supported_languages():
    """Test supported languages list"""
    detector = get_language_detector()
    supported_langs = detector.get_supported_languages()
    
    # Check that all expected languages are supported
    expected_langs = [
        "hin_Deva", "ben_Beng", "tam_Taml", "tel_Telu", "guj_Gujr",
        "kan_Knda", "mal_Mlym", "mar_Deva", "pan_Guru", "ory_Orya",
        "asm_Beng", "urd_Arab", "kas_Arab", "kas_Deva", "gom_Deva",
        "mni_Beng", "mni_Mtei", "npi_Deva", "san_Deva", "sat_Olck",
        "snd_Arab", "snd_Deva", "eng_Latn"
    ]
    
    for lang in expected_langs:
        assert lang in supported_langs, f"Language {lang} not in supported list"
        assert detector.is_language_supported(lang), f"Language {lang} not supported"


def test_language_detection_confidence_thresholds():
    """Test confidence thresholds for different detection methods"""
    detector = get_language_detector()
    
    # High confidence script detection
    result = detector.detect_language("नमस्ते दुनिया आप कैसे हैं मैं ठीक हूं")
    assert result.confidence > 0.8
    
    # Medium confidence word detection
    result = detector.detect_language("मैं हूं")
    assert result.confidence > 0.0
    
    # Low confidence mixed content
    result = detector.detect_language("Hello नमस्ते 123")
    assert result.confidence >= 0.0


def test_language_detection_result_structure():
    """Test that detection result has correct structure"""
    detector = get_language_detector()
    result = detector.detect_language("नमस्ते")
    
    assert isinstance(result, LanguageDetectionResult)
    assert hasattr(result, 'detected_lang')
    assert hasattr(result, 'confidence')
    assert hasattr(result, 'method')
    assert hasattr(result, 'is_auto_detected')
    
    assert isinstance(result.detected_lang, str)
    assert isinstance(result.confidence, float)
    assert isinstance(result.method, str)
    assert isinstance(result.is_auto_detected, bool)
    
    assert 0.0 <= result.confidence <= 1.0
    assert result.is_auto_detected is True
