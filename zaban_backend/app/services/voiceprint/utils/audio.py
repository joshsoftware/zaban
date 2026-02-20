"""Audio loading and processing utilities."""

import io
import logging
import os
import subprocess
import tempfile
from typing import Tuple, Union

import numpy as np
import soundfile as sf
import torch
import torchaudio

logger = logging.getLogger(__name__)


def convert_to_wav(input_path: str) -> str:
    """
    Convert any audio file to standard PCM WAV using ffmpeg.

    Browsers typically record audio in WebM/Opus format, even if the file
    is saved with a .wav extension. This function detects the actual format
    and converts to 16kHz mono PCM WAV for reliable processing.

    Args:
        input_path: Path to the input audio file.

    Returns:
        Path to the converted WAV file (may be same as input if already valid WAV).
    """
    # First, try reading directly with soundfile — if it works, no conversion needed
    try:
        sf.info(input_path)
        return input_path
    except Exception:
        pass  # Not a format soundfile can handle, needs conversion

    logger.info(f"Audio file '{input_path}' is not standard WAV, converting with ffmpeg...")

    # Create a temp output file for the converted audio
    fd, output_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y",           # overwrite output
                "-i", input_path,         # input file
                "-ar", "16000",           # resample to 16kHz
                "-ac", "1",               # mono
                "-sample_fmt", "s16",     # 16-bit PCM
                "-f", "wav",              # force WAV output
                output_path
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            # Clean up on failure
            if os.path.exists(output_path):
                os.remove(output_path)
            raise RuntimeError(
                f"ffmpeg conversion failed (exit code {result.returncode}): {result.stderr}"
            )
        logger.info(f"Successfully converted '{input_path}' to WAV at '{output_path}'")
        return output_path
    except FileNotFoundError:
        if os.path.exists(output_path):
            os.remove(output_path)
        raise RuntimeError(
            "ffmpeg is not installed or not in PATH. "
            "ffmpeg is required to convert browser-recorded audio (WebM/Opus) to WAV."
        )
    except subprocess.TimeoutExpired:
        if os.path.exists(output_path):
            os.remove(output_path)
        raise RuntimeError("ffmpeg conversion timed out after 30 seconds.")


def decode_audio_from_bytes(
    audio_bytes: bytes, path_hint: str = None
) -> Tuple[np.ndarray, int]:
    """
    Decode audio from bytes stored in parquet (e.g. FLAC).

    Args:
        audio_bytes: Bytes containing audio data (FLAC format).
        path_hint: Optional filename hint for format detection.

    Returns:
        Tuple of (audio_array, sampling_rate)
    """
    audio_file = io.BytesIO(audio_bytes)
    audio_array, sampling_rate = sf.read(audio_file)
    return audio_array, sampling_rate


def to_16k_mono(audio_array: np.ndarray, sampling_rate: int) -> np.ndarray:
    """
    Convert audio to mono and resample to 16 kHz.

    Args:
        audio_array: Audio samples (float or int).
        sampling_rate: Current sample rate.

    Returns:
        Mono audio at 16 kHz as float32 numpy array.
    """
    # Convert to mono if stereo
    if len(audio_array.shape) > 1:
        audio_array = np.mean(audio_array, axis=1)
    
    # Convert to float32 if needed
    if audio_array.dtype != np.float32 and audio_array.dtype != np.float64:
        audio_array = audio_array.astype(np.float32) / (np.iinfo(audio_array.dtype).max + 1)
    
    # Resample to 16kHz if needed
    if sampling_rate != 16000:
        tensor = torch.from_numpy(audio_array).float()
        resampler = torchaudio.transforms.Resample(
            orig_freq=sampling_rate, new_freq=16000
        )
        tensor = resampler(tensor)
        audio_array = tensor.numpy()
    
    return audio_array.astype(np.float32)


def load_audio(audio_path: Union[str, np.ndarray, dict]) -> np.ndarray:
    """
    Load audio from file path, numpy array, or HuggingFace dataset format.
    
    Supports: WAV, FLAC, OGG, WebM/Opus, MP3, and other formats via torchaudio fallback.
    
    Args:
        audio_path: Path to audio file, numpy array, or dict with 'array' and 'sampling_rate'
        
    Returns:
        Audio array at 16kHz sampling rate as float32
    """
    if isinstance(audio_path, dict):
        if "array" in audio_path:
            arr = np.asarray(audio_path["array"], dtype=np.float32)
            sr = int(audio_path.get("sampling_rate", 16000))
        elif "bytes" in audio_path:
            arr, sr = decode_audio_from_bytes(audio_path["bytes"], audio_path.get("path"))
        else:
            arr, sr = _load_audio_file(audio_path["path"])
        return to_16k_mono(arr, sr)
    
    if isinstance(audio_path, np.ndarray):
        return to_16k_mono(audio_path.astype(np.float32), 16000)
    
    # String path
    arr, sr = _load_audio_file(audio_path)
    return to_16k_mono(arr, sr)


def _load_audio_file(path: str) -> Tuple[np.ndarray, int]:
    """
    Load audio file, converting to WAV via ffmpeg if needed.
    
    Browsers typically record in WebM/Opus format even when the file extension
    is .wav. This function uses ffmpeg to convert to standard PCM WAV first,
    then reads with soundfile.
    
    Args:
        path: Path to the audio file
        
    Returns:
        Tuple of (audio_array, sampling_rate)
    """
    converted_path = None
    try:
        # Convert to WAV if needed (handles WebM/Opus from browser recordings)
        wav_path = convert_to_wav(path)
        if wav_path != path:
            converted_path = wav_path  # Track for cleanup

        arr, sr = sf.read(wav_path)
        return arr, sr
    except RuntimeError:
        raise  # Re-raise ffmpeg conversion errors as-is
    except Exception as e:
        raise RuntimeError(
            f"Failed to load audio from '{path}': {e}. "
            f"Ensure the file is a valid audio format (WAV, FLAC, OGG, WebM, MP3, etc.) "
            f"and that ffmpeg is installed for WebM/Opus support."
        )
    finally:
        # Clean up temp converted file
        if converted_path and os.path.exists(converted_path):
            os.remove(converted_path)
