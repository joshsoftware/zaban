import os
import tempfile
from typing import Optional
from dataclasses import dataclass

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    print("⚠️  faster-whisper not available; install with: pip install faster-whisper ctranslate2")


@dataclass
class SttResult:
    text: str
    language: str
    language_probability: Optional[float] = None
    segments: Optional[list] = None
    model: str = "faster-whisper"


class FasterWhisperSttService:
    """
    STT service using faster-whisper (CTranslate2 backend).
    Handles both language detection and transcription.
    No numba/llvmlite dependencies.
    """
    
    # Map Whisper 2-letter codes to BCP-47
    WHISPER_TO_BCP47 = {
        'en': 'eng_Latn', 'hi': 'hin_Deva', 'bn': 'ben_Beng', 'ta': 'tam_Taml',
        'te': 'tel_Telu', 'gu': 'guj_Gujr', 'kn': 'kan_Knda', 'ml': 'mal_Mlym',
        'mr': 'mar_Deva', 'pa': 'pan_Guru', 'or': 'ory_Orya', 'as': 'asm_Beng',
        'ur': 'urd_Arab', 'ne': 'nep_Deva', 'si': 'sin_Sinh',
    }
    
    def __init__(self):
        self.model = None
        self.model_name = None
        self.model_loaded = False
        self.device = "cuda" if os.getenv("USE_CUDA", "false").lower() == "true" else "cpu"
        
        if not FASTER_WHISPER_AVAILABLE:
            print("⚠️  faster-whisper not installed. Install with: pip install faster-whisper ctranslate2")
            return
        
        # Preload model if enabled
        if os.getenv("PRELOAD_FASTER_WHISPER", "true").lower() == "true":
            model_size = os.getenv("WHISPER_MODEL", "large-v3")
            self.load_model(model_size)
    
    def load_model(self, model_size: str = "large-v3"):
        """Load faster-whisper model."""
        if not FASTER_WHISPER_AVAILABLE:
            raise RuntimeError("faster-whisper is not installed.")
        
        if self.model_loaded and self.model_name == model_size:
            return  # Already loaded
        
        print(f"📥 Loading faster-whisper model '{model_size}' on {self.device}...")
        try:
            compute_type = "int8" if self.device == "cpu" else "float16"
            self.model = WhisperModel(
                model_size,
                device=self.device,
                compute_type=compute_type,
                download_root=os.path.expanduser("~/.cache/huggingface/hub")
            )
            self.model_name = model_size
            self.model_loaded = True
            print(f"✅ faster-whisper model '{model_size}' loaded successfully on {self.device}")
        except Exception as e:
            print(f"❌ Failed to load faster-whisper model '{model_size}': {e}")
            raise
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        auto_detect_language: bool = True,
        model_size: Optional[str] = None,
        file_suffix: Optional[str] = None,
    ) -> SttResult:
        """
        Transcribe audio using faster-whisper.
        
        Args:
            audio_data: Raw audio bytes
            language: Target language (2-letter or BCP-47). If None, auto-detect.
            auto_detect_language: Enable auto-detection when language is None
            model_size: Override model size (or use preloaded)
            file_suffix: File extension hint for audio format
        
        Returns:
            SttResult with transcription and metadata
        """
        if not FASTER_WHISPER_AVAILABLE:
            raise RuntimeError("faster-whisper is not installed.")
        
        # Load model if needed
        if not self.model_loaded:
            self.load_model(model_size or os.getenv("WHISPER_MODEL", "large-v3"))
        elif model_size and model_size != self.model_name:
            self.load_model(model_size)
        
        # Normalize language
        if language:
            if "_" in language:
                language = language.split("_")[0]  # eng_Latn -> eng
            language = language[:2]  # eng -> en
        
        temp_file_path = None
        try:
            # Write audio to temp file
            suffix = file_suffix or ".wav"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Transcribe with improved language detection
            # For auto-detection, faster-whisper does detection automatically
            # We use better parameters to improve detection accuracy
            if language is None and auto_detect_language:
                # Auto-detect: faster-whisper will detect language automatically
                # Use beam_size=5 for better accuracy in both detection and transcription
                segments, info = self.model.transcribe(
                    temp_file_path,
                    language=None,  # None triggers auto-detection
                    task="transcribe",
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500),
                    beam_size=5,  # Higher beam_size for better accuracy
                    temperature=0.0,
                    best_of=5,  # Try multiple candidates for better detection
                )
            else:
                # Use specified language
                segments, info = self.model.transcribe(
                    temp_file_path,
                    language=language if language else None,
                    task="transcribe",
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500),
                    beam_size=5,
                    temperature=0.0,
                )
            
            # Collect segments
            text_segments = []
            full_text = ""
            for segment in segments:
                text_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
                full_text += segment.text
            
            full_text = full_text.strip()
            
            # Get detected language
            detected_lang = info.language if hasattr(info, 'language') else language
            detected_prob = float(info.language_probability) if hasattr(info, 'language_probability') else None
            
            # Warn if confidence is low (might be wrong detection)
            if detected_prob is not None and detected_prob < 0.6:
                print(f"⚠️  Low language detection confidence: {detected_lang} ({detected_prob:.2f}). Detection may be inaccurate.")
            
            # Map to BCP-47
            bcp47_lang = self.WHISPER_TO_BCP47.get(detected_lang, f"{detected_lang}_Latn")
            
            return SttResult(
                text=full_text,
                language=bcp47_lang,
                language_probability=detected_prob,
                segments=text_segments,
                model=f"faster-whisper-{self.model_name}"
            )
        
        except Exception as e:
            print(f"❌ faster-whisper transcription failed: {e}")
            raise
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass


_faster_whisper_stt_service = None


def get_faster_whisper_stt_service() -> FasterWhisperSttService:
    global _faster_whisper_stt_service
    if _faster_whisper_stt_service is None:
        _faster_whisper_stt_service = FasterWhisperSttService()
    return _faster_whisper_stt_service

