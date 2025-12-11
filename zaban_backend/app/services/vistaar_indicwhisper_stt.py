"""
Vistaar IndicWhisper STT Service using AI4Bharat's fine-tuned Whisper models.
These models are specifically trained on Vistaar datasets for Indian languages.
Reference: https://github.com/AI4Bharat/vistaar
"""
import os
import tempfile
from typing import Optional, Dict
from dataclasses import dataclass
from pathlib import Path

try:
    from transformers import pipeline
    import torch
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


@dataclass
class SttResult:
    text: str
    language: str
    language_probability: Optional[float] = None
    model: str = "vistaar-indicwhisper"


class VistaarIndicWhisperSttService:
    """
    STT using Vistaar IndicWhisper models - Whisper fine-tuned on Indian language datasets.
    These models achieve lowest WER on 39/59 Vistaar benchmarks.
    """

    # Model download URLs from Vistaar
    LANG_TO_MODEL_URL: Dict[str, str] = {
        "bn": "https://indicwhisper.objectstore.e2enetworks.net/bengali_models.zip",
        "gu": "https://indicwhisper.objectstore.e2enetworks.net/gujarati_models.zip",
        "hi": "https://indicwhisper.objectstore.e2enetworks.net/hindi_models.zip",
        "kn": "https://indicwhisper.objectstore.e2enetworks.net/kannada_models.zip",
        "ml": "https://indicwhisper.objectstore.e2enetworks.net/malayalam_models.zip",
        "mr": "https://indicwhisper.objectstore.e2enetworks.net/marathi_models.zip",
        "or": "https://indicwhisper.objectstore.e2enetworks.net/odia_models.zip",
        "pa": "https://indicwhisper.objectstore.e2enetworks.net/punjabi_models.zip",
        "sa": "https://indicwhisper.objectstore.e2enetworks.net/sanskrit_models.zip",
        "ta": "https://indicwhisper.objectstore.e2enetworks.net/tamil_models.zip",
        "te": "https://indicwhisper.objectstore.e2enetworks.net/telugu_models.zip",
        "ur": "https://indicwhisper.objectstore.e2enetworks.net/urdu_models.zip",
    }
    
    # BCP-47 mappings
    LANG_TO_BCP47 = {
        'bn': 'ben_Beng', 'gu': 'guj_Gujr', 'hi': 'hin_Deva', 'kn': 'kan_Knda',
        'ml': 'mal_Mlym', 'mr': 'mar_Deva', 'or': 'ory_Orya', 'pa': 'pan_Guru',
        'sa': 'san_Deva', 'ta': 'tam_Taml', 'te': 'tel_Telu', 'ur': 'urd_Arab',
    }

    def __init__(self) -> None:
        # Allow override via env; prefer CUDA when available
        self.device = os.getenv("VISTAAR_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
        self.models: Dict[str, object] = {}  # Cache ASR pipelines per language
        self.model_cache_dir = Path(os.path.expanduser("~/.cache/vistaar_indicwhisper"))
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Preload models if enabled
        preload_langs = os.getenv("PRELOAD_VISTAAR_LANGS", "").split(",")
        for lang in preload_langs:
            lang = lang.strip()
            if lang:
                try:
                    print(f"🚀 Preloading Vistaar IndicWhisper model for {lang}...")
                    self._load_model(lang)
                except Exception as e:
                    print(f"⚠️  Failed to preload {lang}: {e}")

    def _download_and_extract_model(self, lang: str) -> Path:
        """Download and extract Vistaar IndicWhisper model if not already cached."""
        model_dir = self.model_cache_dir / f"{lang}_models"
        
        # Check if already downloaded - search recursively for whisper model
        if model_dir.exists():
            model_subdirs = list(model_dir.rglob("whisper-*"))
            if model_subdirs:
                # Filter to directories that have config.json
                for model_path in model_subdirs:
                    if model_path.is_dir() and (model_path / "config.json").exists():
                        print(f"✅ Vistaar IndicWhisper model for {lang} already cached at {model_path}")
                        return model_path
        
        # Download and extract
        import requests
        import zipfile
        
        url = self.LANG_TO_MODEL_URL[lang]
        zip_path = self.model_cache_dir / f"{lang}_models.zip"
        
        print(f"📥 Downloading Vistaar IndicWhisper model for {lang}...")
        print(f"   URL: {url}")
        print(f"   This may take a few minutes (model size ~1.5GB)...")
        
        try:
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            with open(zip_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"   Downloaded: {percent:.1f}%", end='\r')
            
            print(f"\n   ✅ Download complete")
            
            # Extract
            print(f"   📦 Extracting model...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(model_dir)
            
            # Clean up zip file
            zip_path.unlink()
            
            print(f"   ✅ Model extracted to {model_dir}")
            
            # Return the actual model subdirectory - search recursively
            model_subdirs = list(model_dir.rglob("whisper-*"))
            for model_path in model_subdirs:
                if model_path.is_dir() and (model_path / "config.json").exists():
                    return model_path
            
            # Fallback if not found
            raise Exception(f"Could not find Whisper model directory with config.json in {model_dir}")
            
        except Exception as e:
            print(f"❌ Failed to download/extract model: {e}")
            raise

    def _load_model(self, lang: str):
        """Load Vistaar IndicWhisper model for specific language."""
        print(f"🔧 _load_model called with lang='{lang}'")
        
        if not HF_AVAILABLE:
            raise RuntimeError("transformers and torch are not installed")
        
        if lang not in self.LANG_TO_MODEL_URL:
            raise ValueError(
                f"Unsupported language for Vistaar IndicWhisper: {lang}. "
                f"Supported: {', '.join(self.LANG_TO_MODEL_URL.keys())}"
            )
        
        if lang in self.models:
            print(f"✅ Model for '{lang}' already loaded (from cache)")
            return self.models[lang]

        # Download model if needed
        print(f"📦 Downloading/extracting model for '{lang}'...")
        model_path = self._download_and_extract_model(lang)
        print(f"📦 Model path: {model_path}")
        
        print(f"📥 Loading Vistaar IndicWhisper pipeline for {lang}...")
        
        try:
            # Create Whisper ASR pipeline with speed/accuracy tunables
            # Optimized defaults for faster CPU inference
            chunk_len = int(os.getenv("VISTAAR_CHUNK_LENGTH_S", "8"))  # Smaller = faster
            stride_len = int(os.getenv("VISTAAR_STRIDE_LENGTH_S", "2"))  # Smaller = faster
            batch_size = int(os.getenv("VISTAAR_BATCH_SIZE", "1"))  # Keep at 1 for CPU
            dtype = torch.float16 if (self.device == "cuda" and os.getenv("VISTAAR_FP16", "true").lower() == "true") else None

            whisper_asr = pipeline(
                "automatic-speech-recognition",
                model=str(model_path),
                device=self.device,
                torch_dtype=dtype,
                chunk_length_s=chunk_len,
                stride_length_s=stride_len,
                batch_size=batch_size,
                ignore_warning=True,  # Suppress chunk_length_s warning for Whisper
            )
            
            # Special case for Odia (not natively supported by Whisper)
            if lang == 'or':
                whisper_asr.model.config.forced_decoder_ids = (
                    whisper_asr.tokenizer.get_decoder_prompt_ids(
                        language=None, task="transcribe"
                    )
                )
            else:
                whisper_asr.model.config.forced_decoder_ids = (
                    whisper_asr.tokenizer.get_decoder_prompt_ids(
                        language=lang, task="transcribe"
                    )
                )
            
            self.models[lang] = whisper_asr
            print(f"✅ Vistaar IndicWhisper model loaded successfully for {lang}")
            return whisper_asr
            
        except Exception as e:
            print(f"❌ Failed to load Vistaar IndicWhisper model for {lang}: {e}")
            raise

    async def transcribe(
        self,
        audio_data: bytes,
        language: str,
        file_suffix: Optional[str] = None,
    ) -> SttResult:
        """
        Transcribe audio using Vistaar IndicWhisper model.
        
        Args:
            audio_data: Raw audio bytes
            language: Language code (2-letter ISO 639-1)
            file_suffix: Optional file extension hint
        
        Returns:
            SttResult with transcription
        """
        print(f"🎤 Vistaar transcribe called with language='{language}'")
        
        # Normalize language code
        if "_" in language:
            language = language.split("_")[0]  # hin_Deva -> hin
        language = language[:2].lower()  # hin -> hi
        
        print(f"🎤 Normalized language for Vistaar: '{language}'")
        
        # Load model for this language
        whisper_asr = self._load_model(language)
        print(f"🎤 Got ASR pipeline for language: '{language}'")
        
        temp_file_path = None
        try:
            # Write audio to temp file
            suffix = file_suffix or ".wav"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Transcribe with tunable generation parameters
            # Optimized for speed on CPU: num_beams=1 (greedy) is 3x faster than 3
            num_beams = int(os.getenv("VISTAAR_NUM_BEAMS", "1"))  # 1=fastest (greedy decoding)
            rep_penalty = float(os.getenv("VISTAAR_REPETITION_PENALTY", "1.0"))  # Lower is faster
            # Note: Whisper max_target_positions is 448, but decoder_input_ids takes ~4-10 tokens
            # So max_new_tokens must be < 444. Using 400 for safety.
            max_tokens = int(os.getenv("VISTAAR_MAX_NEW_TOKENS", "400"))  # Safe limit for Whisper
            
            result = whisper_asr(
                temp_file_path,
                generate_kwargs={
                    "task": "transcribe",
                    "language": language,
                    "num_beams": num_beams,
                    "repetition_penalty": rep_penalty,
                    "max_new_tokens": max_tokens,
                }
            )
            transcription = result["text"].strip()
            
            # Map to BCP-47
            bcp47_lang = self.LANG_TO_BCP47.get(language, f"{language}_Latn")
            
            return SttResult(
                text=transcription,
                language=bcp47_lang,
                model=f"vistaar-indicwhisper-{language}"
            )
        
        except Exception as e:
            print(f"❌ Vistaar IndicWhisper transcription failed for {language}: {e}")
            raise
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass


_vistaar_indicwhisper_stt_service: Optional[VistaarIndicWhisperSttService] = None


def get_vistaar_indicwhisper_stt_service() -> VistaarIndicWhisperSttService:
    global _vistaar_indicwhisper_stt_service
    if _vistaar_indicwhisper_stt_service is None:
        _vistaar_indicwhisper_stt_service = VistaarIndicWhisperSttService()
    return _vistaar_indicwhisper_stt_service

