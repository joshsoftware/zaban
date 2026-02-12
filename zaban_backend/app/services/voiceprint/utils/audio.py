"""Audio loading and processing utilities."""

import io
from typing import Tuple, Union

import numpy as np
import soundfile as sf
import torch
import torchaudio


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
    Load audio file with fallback to torchaudio for WebM/Opus and other formats.
    
    soundfile doesn't support WebM/Opus (common browser recording format),
    so we fall back to torchaudio which uses ffmpeg backend for broader format support.
    
    Args:
        path: Path to the audio file
        
    Returns:
        Tuple of (audio_array, sampling_rate)
    """
    # Try soundfile first (fast, handles WAV/FLAC/OGG well)
    try:
        arr, sr = sf.read(path)
        return arr, sr
    except Exception as sf_error:
        # Fallback to torchaudio for WebM/Opus and other formats
        try:
            waveform, sr = torchaudio.load(path)
            # Convert to numpy (torchaudio returns [channels, samples])
            arr = waveform.numpy()
            # If stereo/multichannel, transpose to [samples, channels] for consistency
            if arr.ndim == 2:
                arr = arr.T if arr.shape[0] <= 2 else arr  # Transpose if channels first
            return arr, sr
        except Exception as ta_error:
            # If both fail, raise with helpful error message
            raise RuntimeError(
                f"Failed to load audio from '{path}'. "
                f"soundfile error: {sf_error}. "
                f"torchaudio error: {ta_error}. "
                f"Ensure the file is a valid audio format (WAV, FLAC, OGG, WebM, MP3, etc.) "
                f"and that ffmpeg is installed for WebM/Opus support."
            )
