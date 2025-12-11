"""
IndicParler TTS Service

Provides Text-to-Speech using IndicParler model for Indian languages.
"""
import os
import io
from typing import Optional
from dataclasses import dataclass


@dataclass
class TTSResult:
    """Result from TTS synthesis"""
    audio_data: bytes
    sample_rate: int
    language: str
    model: str
    speaker: Optional[str] = None


class IndicParlerTTSService:
    """IndicParler TTS service for Indian languages"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.sample_rate = 44100
        
    def _load_model(self):
        """Lazy load the IndicParler model"""
        if self.model is not None:
            return
        
        try:
            import torch
            from parler_tts import ParlerTTSForConditionalGeneration
            from transformers import AutoTokenizer
            import soundfile as sf
            
            # Determine device
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Load model (using the base Parler-TTS model for now)
            # TODO: Replace with actual IndicParler model when available
            model_name = os.getenv("INDICPARLER_MODEL", "parler-tts/parler-tts-mini-v1")
            
            print(f"🔊 Loading TTS model: {model_name} on {self.device}...")
            
            self.model = ParlerTTSForConditionalGeneration.from_pretrained(
                model_name
            ).to(self.device)
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            print(f"✅ TTS model loaded successfully")
            
        except ImportError as e:
            raise ImportError(
                "IndicParler TTS dependencies not installed. "
                "Please install: pip install parler-tts torch transformers soundfile"
            ) from e
    
    async def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        voice_description: Optional[str] = None,
        speaker: Optional[str] = None,
    ) -> TTSResult:
        """
        Synthesize speech from text
        
        Args:
            text: Text to convert to speech
            language: Language code (2-letter ISO 639-1)
            voice_description: Description of desired voice characteristics
            speaker: Speaker name for consistent voice
            
        Returns:
            TTSResult with audio data and metadata
        """
        self._load_model()
        
        import torch
        import soundfile as sf
        
        # Auto-detect language if not provided
        if not language:
            from .language_detection import get_language_detector
            detector = get_language_detector()
            result = detector.detect_language(text)
            # Extract 2-letter code from BCP-47 format (e.g., "hin_Deva" -> "hi")
            detected_lang = result.detected_lang
            if "_" in detected_lang:
                detected_lang = detected_lang.split("_")[0]
            # Map to 2-letter ISO code
            lang_map = {
                "eng": "en", "hin": "hi", "ben": "bn", "tel": "te", "tam": "ta",
                "guj": "gu", "kan": "kn", "mal": "ml", "mar": "mr", "pan": "pa",
                "ory": "or", "asm": "as", "urd": "ur", "npi": "ne", "san": "sa",
                "kas": "ks", "gom": "kok", "mni": "mni", "snd": "sd", "sat": "sat"
            }
            language = lang_map.get(detected_lang[:3], "en")
        
        # Default voice description if not provided
        if not voice_description:
            voice_description = "A clear and natural voice"
        
        # Generate speech
        try:
            input_ids = self.tokenizer(voice_description, return_tensors="pt").input_ids.to(self.device)
            prompt_input_ids = self.tokenizer(text, return_tensors="pt").input_ids.to(self.device)
            
            with torch.no_grad():
                generation = self.model.generate(
                    input_ids=input_ids,
                    prompt_input_ids=prompt_input_ids,
                )
            
            # Convert to numpy and then to WAV bytes
            audio_arr = generation.cpu().numpy().squeeze()
            
            # Write to bytes buffer
            buffer = io.BytesIO()
            sf.write(buffer, audio_arr, self.sample_rate, format='WAV')
            audio_data = buffer.getvalue()
            
            return TTSResult(
                audio_data=audio_data,
                sample_rate=self.sample_rate,
                language=language,
                model="parler-tts-mini-v1",
                speaker=speaker,
            )
            
        except Exception as e:
            raise RuntimeError(f"TTS synthesis failed: {str(e)}") from e


# Singleton instance
_indicparler_service = None


def get_indicparler_tts_service() -> IndicParlerTTSService:
    """Get or create singleton instance of IndicParler TTS service"""
    global _indicparler_service
    if _indicparler_service is None:
        _indicparler_service = IndicParlerTTSService()
    return _indicparler_service

