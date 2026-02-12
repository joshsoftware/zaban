import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class VoiceprintSettings(BaseSettings):
    """Voiceprint specific configuration."""
    
    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    
    # Voiceprint Collections
    ENROLLED_COLLECTION: str = "enrolled_users_ecapa"
    COHORT_COLLECTION: str = "indian_cohort_ecapa"
    
    # Models
    PLDA_MODEL_PATH: str = "./models/plda_model.pkl"
    ECAPA_SOURCE: str = "speechbrain/spkrec-ecapa-voxceleb"
    ECAPA_SAVEDIR: str = "./pretrained_models/spkrec-ecapa-voxceleb"
    
    # Verification Parameters
    VERIFICATION_THRESHOLD: float = 3.0
    COHORT_TOP_K: int = 30
    MIN_ENROLLMENT_SAMPLES: int = 3
    MAX_ENROLLMENT_SAMPLES: int = 10
    TARGET_SAMPLE_RATE: int = 16000
    
    # Security
    XOR_AUDIO_KEY: str = "voiceprint_xor_key_v1"
    
    # Feature Toggle
    VOICEPRINT_ENABLED: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_hf_token(self) -> str:
        """Get HuggingFace token from environment."""
        return os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN") or ""


voiceprint_settings = VoiceprintSettings()
