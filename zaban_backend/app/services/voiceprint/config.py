import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class VoiceprintSettings(BaseSettings):
    """Voiceprint specific configuration."""
    
    # Qdrant (Loaded from .env)
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", 6333))
    
    # Voiceprint Collections
    ENROLLED_COLLECTION: str = "enrolled_users_ecapa"
    COHORT_COLLECTION: str = "indian_cohort_ecapa"
    
    # Models
    PLDA_MODEL_PATH: str = os.getenv("PLDA_MODEL_PATH", "./models/plda_model.pkl")
    ECAPA_SOURCE: str = "speechbrain/spkrec-ecapa-voxceleb"
    ECAPA_SAVEDIR: str = "./pretrained_models/spkrec-ecapa-voxceleb"
    
    # Verification Parameters
    VERIFICATION_THRESHOLD: float = 3.0
    COHORT_TOP_K: int = 30
    MIN_ENROLLMENT_SAMPLES: int = 3
    MAX_ENROLLMENT_SAMPLES: int = 10
    TARGET_SAMPLE_RATE: int = 16000
    
    # Feature Toggle
    VOICEPRINT_ENABLED: bool = True
    # STRICT_VOICEPRINT_USER_CHECK: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_hf_token(self) -> str:
        """Get HuggingFace token from environment."""
        return os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN") or ""


voiceprint_settings = VoiceprintSettings()
