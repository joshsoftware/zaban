"""
Language detection service using various methods
"""
import re
import os
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class LanguageDetectionResult:
    """Result of language detection"""
    detected_lang: str
    confidence: float
    method: str
    is_auto_detected: bool = True


class LanguageDetector:
    """Language detection service"""
    
    # Language patterns for script-based detection
    SCRIPT_PATTERNS = {
        'hin_Deva': r'[\u0900-\u097F]',  # Devanagari
        'ben_Beng': r'[\u0980-\u09FF]',  # Bengali
        'tam_Taml': r'[\u0B80-\u0BFF]',  # Tamil
        'tel_Telu': r'[\u0C00-\u0C7F]',  # Telugu
        'guj_Gujr': r'[\u0A80-\u0AFF]',  # Gujarati
        'kan_Knda': r'[\u0C80-\u0CFF]',  # Kannada
        'mal_Mlym': r'[\u0D00-\u0D7F]',  # Malayalam
        'mar_Deva': r'[\u0900-\u097F]',  # Marathi (Devanagari)
        'pan_Guru': r'[\u0A00-\u0A7F]',  # Punjabi (Gurmukhi)
        'ory_Orya': r'[\u0B00-\u0B7F]',  # Odia
        'asm_Beng': r'[\u0980-\u09FF]',  # Assamese (Bengali script)
        'urd_Arab': r'[\u0600-\u06FF]',  # Urdu (Arabic script)
        'kas_Arab': r'[\u0600-\u06FF]',  # Kashmiri (Arabic script)
        'kas_Deva': r'[\u0900-\u097F]',  # Kashmiri (Devanagari)
        'gom_Deva': r'[\u0900-\u097F]',  # Konkani (Devanagari)
        'mni_Beng': r'[\u0980-\u09FF]',  # Manipuri (Bengali script)
        'mni_Mtei': r'[\uABC0-\uABFF]',  # Manipuri (Meitei script)
        'npi_Deva': r'[\u0900-\u097F]',  # Nepali (Devanagari)
        'san_Deva': r'[\u0900-\u097F]',  # Sanskrit (Devanagari)
        'sat_Olck': r'[\u1C50-\u1C7F]',  # Santali (Ol Chiki)
        'snd_Arab': r'[\u0600-\u06FF]',  # Sindhi (Arabic script)
        'snd_Deva': r'[\u0900-\u097F]',  # Sindhi (Devanagari)
        'eng_Latn': r'[a-zA-Z]',  # English (Latin script)
    }
    
    # Common words for language detection
    LANGUAGE_WORDS = {
        'hin_Deva': ['है', 'हैं', 'का', 'की', 'के', 'में', 'से', 'को', 'पर', 'तो', 'या', 'और', 'लेकिन', 'कि', 'यह', 'वह', 'मैं', 'तुम', 'हम', 'आप'],
        'ben_Beng': ['আছে', 'হয়', 'করে', 'মধ্যে', 'থেকে', 'কে', 'পরে', 'তবে', 'বা', 'এবং', 'কিন্তু', 'যে', 'এটি', 'সে', 'আমি', 'তুমি', 'আমরা', 'আপনি'],
        'tam_Taml': ['உள்ளது', 'ஆக', 'செய்ய', 'மத்தியில்', 'இருந்து', 'க்கு', 'பிறகு', 'ஆனால்', 'அல்லது', 'மற்றும்', 'ஆனால்', 'என்று', 'இது', 'அது', 'நான்', 'நீ', 'நாங்கள்', 'நீங்கள்'],
        'tel_Telu': ['ఉంది', 'అవుతుంది', 'చేస్తుంది', 'మధ్య', 'నుండి', 'కు', 'తర్వాత', 'కానీ', 'లేదా', 'మరియు', 'కానీ', 'అని', 'ఇది', 'అది', 'నేను', 'నువ్వు', 'మేము', 'మీరు'],
        'guj_Gujr': ['છે', 'છે', 'કરે', 'માં', 'થી', 'ને', 'પછી', 'પરંતુ', 'અથવા', 'અને', 'પરંતુ', 'કે', 'આ', 'તે', 'હું', 'તું', 'અમે', 'તમે'],
        'kan_Knda': ['ಇದೆ', 'ಆಗುತ್ತದೆ', 'ಮಾಡುತ್ತದೆ', 'ಮಧ್ಯೆ', 'ಇಂದ', 'ಗೆ', 'ನಂತರ', 'ಆದರೆ', 'ಅಥವಾ', 'ಮತ್ತು', 'ಆದರೆ', 'ಎಂದು', 'ಇದು', 'ಅದು', 'ನಾನು', 'ನೀನು', 'ನಾವು', 'ನೀವು'],
        'mal_Mlym': ['ഉണ്ട്', 'ആകുന്നു', 'ചെയ്യുന്നു', 'ഇടയിൽ', 'ഇൽ', 'എന്ന്', 'ശേഷം', 'എന്നാൽ', 'അല്ലെങ്കിൽ', 'ഒപ്പം', 'എന്നാൽ', 'എന്ന്', 'ഇത്', 'അത്', 'ഞാൻ', 'നീ', 'ഞങ്ങൾ', 'നിങ്ങൾ'],
        'mar_Deva': ['आहे', 'होते', 'करते', 'मध्ये', 'पासून', 'ला', 'नंतर', 'पण', 'किंवा', 'आणि', 'पण', 'की', 'हे', 'ते', 'मी', 'तू', 'आम्ही', 'तुम्ही'],
        'pan_Guru': ['ਹੈ', 'ਹਨ', 'ਕਰਦਾ', 'ਵਿਚ', 'ਤੋਂ', 'ਨੂੰ', 'ਬਾਅਦ', 'ਪਰ', 'ਜਾਂ', 'ਅਤੇ', 'ਪਰ', 'ਕਿ', 'ਇਹ', 'ਉਹ', 'ਮੈਂ', 'ਤੂੰ', 'ਅਸੀਂ', 'ਤੁਸੀਂ'],
        'eng_Latn': ['is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must']
    }
    
    def __init__(self):
        self.script_patterns = {lang: re.compile(pattern) for lang, pattern in self.SCRIPT_PATTERNS.items()}
    
    def detect_language(self, text: str) -> LanguageDetectionResult:
        """
        Detect the language of the given text using multiple methods.
        Returns the most confident detection result.
        """
        if not text or not text.strip():
            return LanguageDetectionResult(
                detected_lang="eng_Latn",
                confidence=0.0,
                method="default",
                is_auto_detected=True
            )
        
        # Method 1: Script-based detection
        script_result = self._detect_by_script(text)
        
        # Method 2: Word-based detection
        word_result = self._detect_by_words(text)
        
        # Method 3: Character frequency analysis
        freq_result = self._detect_by_frequency(text)
        
        # Combine results and choose the best one
        results = [script_result, word_result, freq_result]
        results = [r for r in results if r is not None]
        
        if not results:
            return LanguageDetectionResult(
                detected_lang="eng_Latn",
                confidence=0.0,
                method="default",
                is_auto_detected=True
            )
        
        # Choose the result with highest confidence
        best_result = max(results, key=lambda x: x.confidence)
        return best_result
    
    def _detect_by_script(self, text: str) -> Optional[LanguageDetectionResult]:
        """Detect language based on script/character patterns"""
        text_clean = text.strip()
        if not text_clean:
            return None
        
        script_scores = {}
        for lang, pattern in self.script_patterns.items():
            matches = pattern.findall(text_clean)
            if matches:
                score = len(matches) / len(text_clean)
                script_scores[lang] = score
        
        if not script_scores:
            return None
        
        best_lang = max(script_scores, key=script_scores.get)
        confidence = script_scores[best_lang]
        
        return LanguageDetectionResult(
            detected_lang=best_lang,
            confidence=confidence,
            method="script",
            is_auto_detected=True
        )
    
    def _detect_by_words(self, text: str) -> Optional[LanguageDetectionResult]:
        """Detect language based on common words"""
        text_lower = text.lower().strip()
        if not text_lower:
            return None
        
        word_scores = {}
        for lang, words in self.LANGUAGE_WORDS.items():
            score = 0
            for word in words:
                if word in text_lower:
                    score += 1
            if score > 0:
                word_scores[lang] = score / len(words)
        
        if not word_scores:
            return None
        
        best_lang = max(word_scores, key=word_scores.get)
        confidence = min(word_scores[best_lang], 1.0)
        
        return LanguageDetectionResult(
            detected_lang=best_lang,
            confidence=confidence,
            method="words",
            is_auto_detected=True
        )
    
    def _detect_by_frequency(self, text: str) -> Optional[LanguageDetectionResult]:
        """Detect language based on character frequency analysis"""
        # This is a simplified version - in practice, you'd use more sophisticated analysis
        # For now, we'll use script detection as a fallback
        return self._detect_by_script(text)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages for auto-detection"""
        return list(self.SCRIPT_PATTERNS.keys())
    
    def is_language_supported(self, lang: str) -> bool:
        """Check if a language is supported for auto-detection"""
        return lang in self.SCRIPT_PATTERNS


# Global detector instance
_language_detector = None

def get_language_detector() -> LanguageDetector:
    """Get the global language detector instance"""
    global _language_detector
    if _language_detector is None:
        _language_detector = LanguageDetector()
    return _language_detector
