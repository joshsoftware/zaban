"""ECAPA-TDNN embedding extraction via SpeechBrain."""

import os
from typing import Optional, Union

import numpy as np
import torch
from speechbrain.inference.speaker import EncoderClassifier

from app.services.voiceprint.config import voiceprint_settings as settings


def _ensure_hf_token():
    """Ensure HuggingFace token is available in environment."""
    if not os.environ.get("HF_TOKEN") and not os.environ.get("HUGGING_FACE_HUB_TOKEN"):
        token = settings.get_hf_token()
        if token:
            os.environ["HF_TOKEN"] = token


class ECAPAEmbedder:
    """Extract L2-normalized ECAPA-TDNN embeddings (16 kHz mono input)."""

    def __init__(
        self,
        source: str = None,
        savedir: Optional[str] = None,
        device: Optional[str] = None,
        use_auth_token: bool = True,
    ):
        """
        Initialize ECAPA embedder.
        
        Args:
            source: HuggingFace model source (default: speechbrain/spkrec-ecapa-voxceleb)
            savedir: Directory to save pretrained model
            device: Device to use ('cuda' or 'cpu')
            use_auth_token: Whether to use HuggingFace auth token
        """
        _ensure_hf_token()
        
        self.source = source or settings.ECAPA_SOURCE
        self.savedir = savedir or settings.ECAPA_SAVEDIR
        
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        
        # Check if we have a token available
        has_token = bool(
            os.environ.get("HF_TOKEN") or 
            os.environ.get("HUGGING_FACE_HUB_TOKEN") or 
            settings.get_hf_token()
        )
        
        self._classifier = EncoderClassifier.from_hparams(
            source=self.source,
            savedir=self.savedir,
            run_opts={"device": str(self.device)},
            use_auth_token=use_auth_token and has_token,
        )
        
        # Get embedding dimension
        self.embedding_dim = self._classifier.encode_batch(
            torch.randn(1, 16000, device=self.device)
        ).shape[-1]

    def extract_embedding(
        self,
        audio: Union[np.ndarray, torch.Tensor],
        sample_rate: int = 16000,
    ) -> np.ndarray:
        """
        Extract a single L2-normalized embedding.

        Args:
            audio: Mono waveform (samples,) at 16 kHz, float32.
            sample_rate: Must be 16000.

        Returns:
            Embedding as numpy float32, L2-normalized, shape (embedding_dim,).
        """
        if isinstance(audio, np.ndarray):
            audio = torch.from_numpy(audio).float()
        if audio.dim() == 1:
            audio = audio.unsqueeze(0)
        audio = audio.to(self.device)
        
        with torch.no_grad():
            emb = self._classifier.encode_batch(audio)
        
        emb = emb.squeeze(0).cpu().numpy().astype(np.float32)
        
        # L2 normalize
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        
        return emb
