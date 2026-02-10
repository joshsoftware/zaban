"""
STT service using openai-whisper only.
"""
import os
import tempfile
from typing import Optional
from dataclasses import dataclass

try:
    import whisper
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    print("⚠️  openai-whisper not available; install with: pip install openai-whisper")

import torch

from .constants import (
    WAV_FORMAT_NAME,
    MP3_FORMAT_NAME,
    WHISPER_TO_BCP47,
    DEFAULT_TRANSLATE_PROMPT,
    WHISPER_BEAM_SIZE,
    WHISPER_BEST_OF,
    AUDIO_FORMAT_CONFIG,
    DEFAULT_AUDIO_SUFFIX,
)


@dataclass
class SttResult:
    text: str
    language: str
    language_probability: Optional[float] = None
    segments: Optional[list] = None
    model: str = "whisper"


class FasterWhisperSttService:
    """STT service using openai-whisper."""

    WHISPER_TO_BCP47 = WHISPER_TO_BCP47

    def __init__(self):
        self.model = None
        self.model_name = None
        self.model_loaded = False
        # Prefer CUDA when available, then Metal (MPS) on macOS, otherwise CPU.
        if torch.cuda.is_available():
            self.device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        if not FASTER_WHISPER_AVAILABLE:
            print("⚠️  openai-whisper not installed. Install with: pip install openai-whisper")
            return

        if os.getenv("PRELOAD_WHISPER", "true").lower() == "true":
            model_size = os.getenv("WHISPER_MODEL", "medium")
            self.load_model(model_size)

    def load_model(self, model_size: str = "medium"):
        """Load openai-whisper model."""
        if not FASTER_WHISPER_AVAILABLE:
            raise RuntimeError("openai-whisper is not installed.")

        if self.model_loaded and self.model_name == model_size:
            return

        print(f"📥 Loading openai-whisper model '{model_size}' on {self.device}...")
        try:
            self.model = whisper.load_model(model_size, device=self.device)
            self.model_name = model_size
            self.model_loaded = True
            print(f"✅ openai-whisper model '{model_size}' loaded on {self.device}")
        except Exception as e:
            print(f"❌ Failed to load openai-whisper model '{model_size}': {e}")
            raise

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        auto_detect_language: bool = True,
        model_size: Optional[str] = None,
        file_suffix: Optional[str] = None,
        translate_to_english: bool = False,
    ) -> SttResult:
        """Transcribe audio using openai-whisper."""
        if not FASTER_WHISPER_AVAILABLE:
            raise RuntimeError("openai-whisper is not installed.")

        if not self.model_loaded:
            self.load_model(model_size or os.getenv("WHISPER_MODEL", "medium"))
        elif model_size and model_size != self.model_name:
            self.load_model(model_size)

        lang_arg = None
        if language:
            lang_arg = language.split("_")[0][:2].lower() if "_" in language else language[:2].lower()

        temp_file_path = None
        try:
            if not audio_data or len(audio_data) == 0:
                raise ValueError("Audio data is empty")

            audio_len = len(audio_data)
            print(f"[STT] Received audio: {audio_len} bytes, writing temp file...")

            suffix = file_suffix or DEFAULT_AUDIO_SUFFIX
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode='wb') as f:
                f.write(audio_data)
                f.flush()
                os.fsync(f.fileno())
                temp_file_path = f.name

            if not os.path.exists(temp_file_path):
                raise ValueError(f"Failed to write audio file: {temp_file_path}")
            file_size = os.path.getsize(temp_file_path)
            if file_size == 0:
                raise ValueError(f"Audio file is empty: {temp_file_path}")
            if file_size != len(audio_data):
                raise ValueError(f"File size mismatch: expected {len(audio_data)} bytes, got {file_size}")

            # Detect audio format from magic bytes if suffix is .wav
            if suffix == DEFAULT_AUDIO_SUFFIX and len(audio_data) >= 12:
                wav_config = AUDIO_FORMAT_CONFIG[WAV_FORMAT_NAME]
                wav_magic = wav_config["magic"]
                wav_check = wav_config["check"]
                wav_check_offset = wav_config["check_offset"]
                
                # Check if it's actually WAV
                is_wav = (
                    audio_data[:len(wav_magic)] == wav_magic
                    and wav_check
                    and audio_data[wav_check_offset:wav_check_offset+len(wav_check)] == wav_check
                )
                
                if not is_wav:
                    # Try to detect actual format
                    detected_format = None
                    for format_name, config in AUDIO_FORMAT_CONFIG.items():
                        if format_name == WAV_FORMAT_NAME:
                            continue
                        
                        magic = config["magic"]
                        check = config.get("check")
                        check_offset = config.get("check_offset")
                        
                        # Check primary magic bytes
                        if audio_data[:len(magic)] == magic:
                            # If there's a check, verify it
                            if check and check_offset:
                                if audio_data[check_offset:check_offset+len(check)] == check:
                                    detected_format = format_name
                                    break
                            else:
                                detected_format = format_name
                                break
                        
                        # Check alternative magic for MP3 (MPEG header)
                        if format_name == MP3_FORMAT_NAME and "alt_magic" in config:
                            alt_magic = config["alt_magic"]
                            if audio_data[:len(alt_magic)] == alt_magic:
                                detected_format = format_name
                                break
                    
                    # Rename file if format detected
                    if detected_format:
                        new_extension = AUDIO_FORMAT_CONFIG[detected_format]["extension"]
                        suffix = new_extension
                        new_path = temp_file_path.rsplit(".", 1)[0] + new_extension
                        os.rename(temp_file_path, new_path)
                        temp_file_path = new_path

            task = "translate" if translate_to_english else "transcribe"
            # Optional prompt for task=translate to bias toward translation (not transliteration).
            # Whisper uses prompts for style/vocabulary biasing, not instructions. Max ~224 tokens.
            # Note: Whisper often transliterates proper nouns even with task="translate" - this is a known limitation.
            translate_prompt = (
                os.getenv("WHISPER_TRANSLATE_PROMPT", DEFAULT_TRANSLATE_PROMPT).strip()
                or None
            )
            
            # For translation, if no language specified, let Whisper auto-detect (better than forcing wrong language)
            # If language is specified but wrong (e.g., hi when it's mr), translation quality may suffer
            transcribe_kw: dict = {
                "language": lang_arg if lang_arg else None,  # None = auto-detect
                "task": task,
                "verbose": False,
            }
            # Add beam search options for translation to improve quality
            if translate_to_english:
                transcribe_kw["beam_size"] = WHISPER_BEAM_SIZE
                transcribe_kw["best_of"] = WHISPER_BEST_OF
                if translate_prompt:
                    transcribe_kw["prompt"] = translate_prompt
                print(f"[STT] Starting translation (task={task}, lang={lang_arg or 'auto-detect'}, beam_size={WHISPER_BEAM_SIZE}, best_of={WHISPER_BEST_OF}, prompt={'set' if translate_prompt else 'none'})...")
            else:
                print(f"[STT] Starting transcription (task={task}, lang={lang_arg or 'auto-detect'})...")
            try:
                result = self.model.transcribe(temp_file_path, **transcribe_kw)
            except Exception as transcribe_error:
                error_msg = str(transcribe_error)
                if "Failed to load audio" in error_msg or "ffmpeg" in error_msg.lower():
                    raise RuntimeError(
                        f"Failed to decode audio file. The audio data may be corrupted, incomplete, "
                        f"or in an unsupported format. File: {temp_file_path}, Size: {file_size} bytes, "
                        f"Suffix: {suffix}. Original error: {error_msg}"
                    ) from transcribe_error
                raise

            print(f"[STT] Transcription complete, building response...")
            raw_segments = result.get("segments") or []
            text_segments = [
                {"start": s["start"], "end": s["end"], "text": (s.get("text") or "").strip()}
                for s in raw_segments
            ]
            full_text = (result.get("text") or "").strip()
            detected_lang = result.get("language") or lang_arg or "en"
            bcp47_lang = self.WHISPER_TO_BCP47.get(detected_lang, f"{detected_lang}_Latn")
            
            # Log if translation might have transliterated (common with proper nouns)
            if translate_to_english:
                # Check if output looks like transliteration (contains non-English characters or patterns)
                # This is just a warning - Whisper often transliterates proper nouns
                if any(ord(c) > 127 for c in full_text[:50]):  # Check first 50 chars for non-ASCII
                    print(f"⚠️  [STT] Translation output may contain transliteration (common for proper nouns): {full_text[:100]}")

            print(f"[STT] Done. language={bcp47_lang}, text_len={len(full_text)}, task={task}")
            return SttResult(
                text=full_text,
                language=bcp47_lang,
                language_probability=None,
                segments=text_segments,
                model=f"whisper-{self.model_name}",
            )
        except ValueError:
            raise
        except RuntimeError:
            raise
        except Exception as e:
            print(f"❌ openai-whisper transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {str(e)}") from e
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
