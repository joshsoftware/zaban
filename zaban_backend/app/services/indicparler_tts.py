"""
IndicParler TTS Service

Provides Text-to-Speech using IndicParler model for Indian languages.
"""
import os
import io
import re
import numpy as np
from typing import Optional, List
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
        self.description_tokenizer = None
        self.device = None
        self.sample_rate = None # Will be loaded from model config
        
    def _load_model(self):
        """Lazy load the IndicParler model"""
        if self.model is not None:
            return

        try:
            import torch
            from parler_tts import ParlerTTSForConditionalGeneration
            from transformers import AutoTokenizer

            # Determine device
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

            # Load model (using the AI4Bharat IndicParler model)
            model_name = os.getenv("INDICPARLER_MODEL", "ai4bharat/indic-parler-tts")

            print(f"🔊 Loading TTS model: {model_name} on {self.device}...")

            # Use FP16 for faster inference on GPU
            torch_dtype = torch.float16 if self.device == "cuda" else torch.float32

            self.model = ParlerTTSForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch_dtype
            ).to(self.device)
            self.model.eval()

            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.description_tokenizer = AutoTokenizer.from_pretrained(
                self.model.config.text_encoder._name_or_path
            )

            # Get sample rate from model config or default to 44100
            self.sample_rate = getattr(self.model.config, "sampling_rate", 44100)

            print(f"✅ TTS model loaded successfully (dtype={torch_dtype}, rate={self.sample_rate}Hz)")
            
        except ImportError as e:
            raise ImportError(
                "IndicParler TTS dependencies not installed. "
                "Please install: pip install parler-tts torch transformers soundfile"
            ) from e
    
    
    
    def _chunk_text(self, text: str, language: str = "en", max_chars: int = 300) -> List[str]:
        """
        Split text into chunks. Short text (<= max_single) is returned as one chunk to avoid overhead.
        """
        text = text.strip()
        if not text:
            return []

        max_single = int(os.getenv("INDICPARLER_MAX_SINGLE_CHUNK", "120"))
        if len(text) <= max_single and "\n" not in text:
            return [text]

        try:
            from indicnlp.tokenize import sentence_tokenize
            sentences = sentence_tokenize.sentence_split(text, lang=language)
        except Exception:
            delimiters = r'[.?!\u0964\u06D4\n]+'
            parts = re.split(f'({delimiters})', text)
            sentences = []
            for i in range(0, len(parts) - 1, 2):
                s = (parts[i] + parts[i + 1]).strip()
                if s:
                    sentences.append(s)
            if len(parts) % 2 != 0 and parts[-1].strip():
                sentences.append(parts[-1].strip())

        chunks = []
        current_chunk = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(current_chunk) + len(sentence) + 1 > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = f"{current_chunk} {sentence}" if current_chunk else sentence
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

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
                "kas": "ks", "gom": "kok", "mni": "mni", "snd": "sd", "sat": "sat",
                "doi": "doi", "brx": "brx", "mai": "mai"
            }
            language = lang_map.get(detected_lang[:3], "en")
        

        # Map of language codes to full names for prompt generation
        # Supported languages: as, bn, brx, doi, en, gu, hi, kn, ks, kok, mai, ml, mni, mr, ne, or, pa, sa, sat, sd, ta, te, ur
        lang_code_to_name = {
            "as": "Assamese", "asm": "Assamese",
            "bn": "Bengali", "ben": "Bengali",
            "brx": "Bodo",
            "doi": "Dogri",
            "en": "English", "eng": "English",
            "gu": "Gujarati", "guj": "Gujarati",
            "hi": "Hindi", "hin": "Hindi",
            "kn": "Kannada", "kan": "Kannada",
            "ks": "Kashmiri", "kas": "Kashmiri",
            "kok": "Konkani", "gom": "Konkani",
            "mai": "Maithili",
            "ml": "Malayalam", "mal": "Malayalam",
            "mni": "Manipuri",
            "mr": "Marathi", "mar": "Marathi",
            "ne": "Nepali", "npi": "Nepali",
            "or": "Odia", "ory": "Odia",
            "pa": "Punjabi", "pan": "Punjabi",
            "sa": "Sanskrit", "san": "Sanskrit",
            "sat": "Santali",
            "sd": "Sindhi", "snd": "Sindhi",
            "ta": "Tamil", "tam": "Tamil",
            "te": "Telugu", "tel": "Telugu",
            "ur": "Urdu", "urd": "Urdu"
        }

        # Determine full language name for the prompt
        lang_name = lang_code_to_name.get(language.lower(), "Hindi") # Default to Hindi if unknown, or maybe English? Let's default to Hindi for Indic context or English. 
        # Actually given the model is IndicParler, defaulting to a major Indic language might be safer if detected lang fails, but let's stick to the 'language' param.
        # If language is passed as 'en', we get 'English'.
        
        # Default voice description if not provided
        if not voice_description:
            # Construct a standard prompt using the language name
            # Format recommended by AI4Bharat: "A {gender} speaker delivering a slightly expressive speech in {Language} with a moderate speed and pitch."
            # User requested "male" and "calm" default.
            voice_description = f"A male speaker delivering a calm speech in {lang_name}"
        
        # Chunk the text to handle long inputs
        chunks = self._chunk_text(text, language=language)
        if not chunks:
            raise RuntimeError("No text chunks to synthesize")

        # Precompute voice description tokens once (same for all chunks)
        desc_ids = self.description_tokenizer(
            voice_description, return_tensors="pt", padding=True, truncation=True
        )
        desc_ids = {k: v.to(self.device) for k, v in desc_ids.items()}

        silence_duration = float(os.getenv("INDICPARLER_CHUNK_SILENCE_SEC", "0.2"))
        audio_segments = []

        try:
            with torch.inference_mode():
                for i, chunk in enumerate(chunks):
                    if not chunk.strip():
                        continue
                    prompt_ids = self.tokenizer(
                        chunk, return_tensors="pt", padding=True, truncation=True
                    )
                    prompt_ids = {k: v.to(self.device) for k, v in prompt_ids.items()}
                    generation = self.model.generate(
                        input_ids=desc_ids["input_ids"],
                        attention_mask=desc_ids.get("attention_mask"),
                        prompt_input_ids=prompt_ids["input_ids"],
                        prompt_attention_mask=prompt_ids.get("attention_mask"),
                    )
                    audio_arr = generation.cpu().float().numpy().squeeze()
                    audio_segments.append(audio_arr)
                    if i < len(chunks) - 1 and silence_duration > 0:
                        silence_samples = int(silence_duration * self.sample_rate)
                        silence_arr = np.zeros(silence_samples, dtype=audio_arr.dtype)
                        audio_segments.append(silence_arr)

            if not audio_segments:
                raise RuntimeError("No audio generated from text chunks")
            final_audio = np.concatenate(audio_segments)

            buffer = io.BytesIO()
            sf.write(buffer, final_audio, self.sample_rate, format="WAV")
            audio_data = buffer.getvalue()
            
            return TTSResult(
                audio_data=audio_data,
                sample_rate=self.sample_rate,
                language=language,
                model=os.getenv("INDICPARLER_MODEL", "ai4bharat/indic-parler-tts"),
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

