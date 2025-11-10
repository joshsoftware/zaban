"""
Language detection service using FastText only
"""

import os
from typing import Optional, Dict, List
from dataclasses import dataclass

# Try to import FastText, fall back gracefully if not available
try:
    import fasttext
    import requests
    FASTTEXT_AVAILABLE = True
except ImportError:
    FASTTEXT_AVAILABLE = False
    print("⚠️  FastText not available; auto-detection disabled")


@dataclass
class LanguageDetectionResult:
    """Result of language detection"""
    detected_lang: str
    confidence: float
    method: str
    is_auto_detected: bool = True


class LanguageDetector:
    """Language detection service using FastText only"""
    
    # FastText language code to BCP-47 mapping
    # Note: Detection itself is done by FastText. This mapping only normalizes
    # FastText labels (e.g., "hi", "en") to the BCP-47/FLORES tags required by
    # downstream components (e.g., IndicTrans2 expects "hin_Deva", "eng_Latn").
    # We are NOT dependent on this mapping for detection quality, only for
    # formatting the detected label to the tag schema used by the translator.
    FASTTEXT_TO_BCP47 = {
        'hi': 'hin_Deva',      # Hindi
        'bn': 'ben_Beng',      # Bengali
        'ta': 'tam_Taml',      # Tamil
        'te': 'tel_Telu',      # Telugu
        'gu': 'guj_Gujr',      # Gujarati
        'kn': 'kan_Knda',      # Kannada
        'ml': 'mal_Mlym',      # Malayalam
        'mr': 'mar_Deva',      # Marathi
        'pa': 'pan_Guru',      # Punjabi
        'or': 'ory_Orya',      # Odia
        'as': 'asm_Beng',      # Assamese
        'ur': 'urd_Arab',      # Urdu
        'ks': 'kas_Arab',      # Kashmiri
        'gom': 'gom_Deva',     # Konkani
        'mni': 'mni_Beng',     # Manipuri
        'ne': 'npi_Deva',      # Nepali
        'sa': 'san_Deva',      # Sanskrit
        'sat': 'sat_Olck',     # Santali
        'sd': 'snd_Arab',      # Sindhi
        'en': 'eng_Latn',      # English
        'es': 'spa_Latn',      # Spanish
        'fr': 'fra_Latn',      # French
        'de': 'deu_Latn',      # German
        'it': 'ita_Latn',      # Italian
        'pt': 'por_Latn',      # Portuguese
        'ru': 'rus_Cyrl',      # Russian
        'zh': 'zho_Hans',      # Chinese (Simplified)
        'ja': 'jpn_Jpan',      # Japanese
        'ko': 'kor_Hang',      # Korean
        'ar': 'ara_Arab',      # Arabic
        'th': 'tha_Thai',      # Thai
        'vi': 'vie_Latn',      # Vietnamese
        'id': 'ind_Latn',      # Indonesian
        'ms': 'msa_Latn',      # Malay
        'tl': 'fil_Latn',      # Filipino
        'he': 'heb_Hebr',      # Hebrew
        'fa': 'fas_Arab',      # Persian
        'tr': 'tur_Latn',      # Turkish
        'sw': 'swa_Latn',      # Swahili
        'am': 'amh_Ethi',      # Amharic
        'yo': 'yor_Latn',      # Yoruba
        'zu': 'zul_Latn',      # Zulu
        'af': 'afr_Latn',      # Afrikaans
    }
    
    # (No script/word-based constants; FastText-only)
    
    def __init__(self):
        self.fasttext_model = None
        if FASTTEXT_AVAILABLE:
            self._load_fasttext_model()
    
    def _load_fasttext_model(self):
        """Load FastText language identification model"""
        try:
            # Try to load from local cache first
            model_path = os.getenv("FASTTEXT_MODEL_PATH", "lid.176.bin")
            if os.path.exists(model_path):
                self.fasttext_model = fasttext.load_model(model_path)
                print(f"✅ FastText model loaded from {model_path}")
            else:
                # Download model if not available
                print("📥 FastText model not found, downloading...")
                self._download_fasttext_model()
        except Exception as e:
            print(f"⚠️  FastText model loading failed: {e}")
            print("❌ FastText unavailable for detection")
            self.fasttext_model = None
    
    def _download_fasttext_model(self):
        """Download FastText language identification model"""
        try:
            model_url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
            model_path = "lid.176.bin"
            
            print(f"📥 Downloading FastText model from {model_url}")
            response = requests.get(model_url, stream=True)
            response.raise_for_status()
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.fasttext_model = fasttext.load_model(model_path)
            print(f"✅ FastText model downloaded and loaded from {model_path}")
            
        except Exception as e:
            print(f"❌ FastText model download failed: {e}")
            print("❌ FastText model unavailable; detection disabled")
            self.fasttext_model = None
    
    def detect_language(self, text: str) -> LanguageDetectionResult:
        """
        Detect the language of the given text using FastText only.
        Returns a default result (eng_Latn with 0.0 confidence) for empty text.
        Raises an error if FastText is unavailable.
        """
        # Handle empty or whitespace-only text with default fallback
        if not text or not text.strip():
            return LanguageDetectionResult(
                detected_lang='eng_Latn',
                confidence=0.0,
                method='default',
                is_auto_detected=False
            )

        # FastText-only detection
        fasttext_result = self._detect_by_fasttext(text)
        if fasttext_result is None:
            raise RuntimeError("FastText detection unavailable. Ensure FastText is installed and model is loaded.")
        return fasttext_result
    
    def _detect_by_fasttext(self, text: str) -> Optional[LanguageDetectionResult]:
        """Detect language using FastText model"""
        if not self.fasttext_model or not FASTTEXT_AVAILABLE:
            return None
        
        try:
            # FastText requires at least 1 character
            if len(text.strip()) < 1:
                return None
            
            # Get prediction from FastText
            predictions = self.fasttext_model.predict(text.strip(), k=1)
            if not predictions or not predictions[0]:
                return None
            
            # Extract language code and confidence
            fasttext_lang = predictions[0][0].replace('__label__', '')
            confidence = float(predictions[1][0])
            
            # Convert FastText language code to BCP-47 used by IndicTrans2
            # (pure normalization step; detection already decided by FastText)
            bcp47_lang = self.FASTTEXT_TO_BCP47.get(fasttext_lang, fasttext_lang)
            
            return LanguageDetectionResult(
                detected_lang=bcp47_lang,
                confidence=confidence,
                method="fasttext",
                is_auto_detected=True
            )
            
        except Exception as e:
            print(f"⚠️  FastText detection failed: {e}")
            return None
    
    # Removed script/word/frequency detection helpers
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages for auto-detection (FastText only)"""
        if self.fasttext_model and FASTTEXT_AVAILABLE:
            return list(self.FASTTEXT_TO_BCP47.values())
        return []
    
    def is_language_supported(self, lang: str) -> bool:
        """Check if a language is supported for auto-detection (FastText only)"""
        if self.fasttext_model and FASTTEXT_AVAILABLE:
            return lang in self.FASTTEXT_TO_BCP47.values()
        return False
    
    def get_detection_method(self) -> str:
        """Get the current detection method being used"""
        return "fasttext" if (self.fasttext_model and FASTTEXT_AVAILABLE) else "unavailable"
    
    def _get_supported_indic_languages(self) -> List[str]:
        """Get list of languages supported by IndicTrans2"""
        return [
            'eng_Latn',    # English
            'hin_Deva',    # Hindi
            'ben_Beng',    # Bengali
            'tam_Taml',    # Tamil
            'tel_Telu',    # Telugu
            'guj_Gujr',    # Gujarati
            'kan_Knda',    # Kannada
            'mal_Mlym',    # Malayalam
            'mar_Deva',    # Marathi
            'pan_Guru',    # Punjabi
            'ory_Orya',    # Odia
            'asm_Beng',    # Assamese
            'urd_Arab',    # Urdu
            'kas_Arab',    # Kashmiri (Arabic)
            'kas_Deva',    # Kashmiri (Devanagari)
            'gom_Deva',    # Konkani
            'mni_Beng',    # Manipuri (Bengali)
            'mni_Mtei',    # Manipuri (Meitei)
            'npi_Deva',    # Nepali
            'san_Deva',    # Sanskrit
            'sat_Olck',    # Santali
            'snd_Arab',    # Sindhi (Arabic)
            'snd_Deva',    # Sindhi (Devanagari)
        ]


# Global detector instance
_language_detector = None

def get_language_detector() -> LanguageDetector:
    """Get the global language detector instance"""
    global _language_detector
    if _language_detector is None:
        _language_detector = LanguageDetector()
    return _language_detector
