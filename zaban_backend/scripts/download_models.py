#!/usr/bin/env python3
"""
Pre-download all ML models required by Zaban backend.
Run this during Docker build to bake models into the image.
"""
import os
import sys
from pathlib import Path


def check_model_exists(model_name):
    """Check if a Hugging Face model already exists in cache"""
    cache_dir = Path(os.getenv("HF_HOME", Path.home() / ".cache/huggingface"))
    # HF stores models in hub directory with format: models--org--modelname
    model_dir = cache_dir / "hub" / f"models--{model_name.replace('/', '--')}"
    exists = model_dir.exists() and any(model_dir.iterdir())
    if exists:
        print(f"   ✓ Model already cached: {model_name}")
    return exists


def download_indictrans2_models():
    """Download IndicTrans2 translation models"""
    print("\n" + "="*70)
    print("📥 Downloading IndicTrans2 Models")
    print("="*70)

    try:
        from huggingface_hub import snapshot_download

        hf_token = os.getenv("HUGGING_FACE_TOKEN")

        # Models to download
        models = [
            os.getenv("INDICTRANS2_EN_INDIC_MODEL", "ai4bharat/indictrans2-en-indic-dist-200M"),
            os.getenv("INDICTRANS2_INDIC_EN_MODEL", "ai4bharat/indictrans2-indic-en-dist-200M"),
        ]

        for model_name in models:
            print(f"\n📦 Checking: {model_name}")

            # Skip if already exists
            if check_model_exists(model_name):
                continue

            print(f"   Downloading from Hugging Face (Download-only)...")
            snapshot_download(
                repo_id=model_name,
                token=hf_token,
                repo_type="model"
            )
            print(f"✅ Successfully downloaded: {model_name}")

        print("\n✅ All IndicTrans2 models ready!")
        return True

    except Exception as e:
        print(f"❌ Failed to download IndicTrans2 models: {e}")
        return False


def download_indicparler_tts_model():
    """Download IndicParler TTS model"""
    print("\n" + "="*70)
    print("📥 Downloading IndicParler TTS Model")
    print("="*70)

    try:
        from huggingface_hub import snapshot_download

        hf_token = os.getenv("HUGGING_FACE_TOKEN")
        if not hf_token:
            print("⚠️  WARNING: HUGGING_FACE_TOKEN not set!")
            print("   The IndicParler TTS model is gated and requires authentication.")
            print("   Set HUGGING_FACE_TOKEN as a build arg to download this model.")
            return False

        model_name = os.getenv("INDICPARLER_MODEL", "ai4bharat/indic-parler-tts")

        print(f"\n📦 Checking: {model_name}")

        # Skip if already exists
        if check_model_exists(model_name):
            print("✅ IndicParler TTS model already cached!")
            return True

        print("   Downloading from Hugging Face (Download-only)...")
        print("   (This is a large model, may take several minutes...)")

        # Download main model
        snapshot_download(
            repo_id=model_name,
            token=hf_token,
            repo_type="model"
        )

        print(f"✅ Successfully downloaded: {model_name}")
        return True

    except Exception as e:
        print(f"❌ Failed to download IndicParler TTS model: {e}")
        print(f"   Make sure you have:")
        print(f"   1. Requested access at: https://huggingface.co/{model_name}")
        print(f"   2. Set HUGGING_FACE_TOKEN environment variable")
        return False


def download_whisper_model():
    """Download Whisper STT model"""
    print("\n" + "="*70)
    print("📥 Downloading Whisper STT Model")
    print("="*70)

    try:
        import whisper
        from whisper import _MODELS, _download

        model_size = os.getenv("WHISPER_MODEL", "medium")

        # Check if model exists in Whisper's cache
        whisper_cache = Path.home() / ".cache" / "whisper"
        model_file = whisper_cache / f"{model_size}.pt"

        print(f"\n📦 Checking Whisper model: {model_size}")

        if model_file.exists():
            print(f"   ✓ Model already cached: {model_file}")
            print(f"✅ Whisper {model_size} model ready!")
            return True

        print(f"   Downloading from OpenAI (Download-only)...")
        # Use internal _download to avoid loading the model into memory
        _download(_MODELS[model_size], str(whisper_cache), False)
        print(f"✅ Successfully downloaded Whisper {model_size} model!")
        return True

    except Exception as e:
        print(f"❌ Failed to download Whisper model: {e}")
        return False


def download_fasttext_model():
    """Download FastText language detection model"""
    print("\n" + "="*70)
    print("📥 Downloading FastText Language Detection Model")
    print("="*70)

    try:
        import fasttext
        import requests
        from pathlib import Path

        # Determine cache directory
        cache_dir = Path(os.getenv("FASTTEXT_CACHE_DIR", Path.home() / ".cache/zaban/models"))
        cache_dir.mkdir(parents=True, exist_ok=True)

        model_url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
        model_filename = "lid.176.bin"
        model_path = cache_dir / model_filename

        if model_path.exists():
            print(f"✅ FastText model already exists at: {model_path}")
            return True

        print(f"\n📦 Downloading from: {model_url}")
        print(f"📁 Saving to: {model_path}")

        # Download
        response = requests.get(model_url, stream=True, timeout=120)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        print(f"📊 Download size: {total_size / (1024*1024):.2f} MB")

        temp_path = cache_dir / f"{model_filename}.tmp"
        downloaded = 0

        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # Print progress every 10MB
                    if downloaded % (10*1024*1024) == 0:
                        progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                        print(f"⏳ Progress: {progress:.1f}%")

        # Move to final location
        temp_path.rename(model_path)

        # Verify by loading
        fasttext.load_model(str(model_path))

        print(f"✅ Successfully downloaded FastText model!")
        return True

    except Exception as e:
        print(f"❌ Failed to download FastText model: {e}")
        return False

def download_voiceprint_models():
    """Download SpeechBrain ECAPA Voiceprint model from Hugging Face"""
    print("\n" + "=" * 70)
    print("📥 Downloading SpeechBrain ECAPA Voiceprint Model")
    print("=" * 70)

    try:
        from speechbrain.inference.speaker import EncoderClassifier  # Fixed import
        
        model_repo = "speechbrain/spkrec-ecapa-voxceleb"
        local_dir = os.getenv(
            "VOICEPRINT_MODEL_DIR",
            "./pretrained_models/spkrec-ecapa-voxceleb"  # Fixed to match config
        )
        
        # Ensure directory exists
        os.makedirs(local_dir, exist_ok=True)

        hf_token = os.getenv("HUGGING_FACE_TOKEN")

        print(f"\n📦 Checking: {model_repo}")
        print(f"📂 Local directory: {local_dir}")

        # Skip download if already present
        if os.path.exists(local_dir) and os.listdir(local_dir):
            print("✅ ECAPA Voiceprint model already cached!")
            return True

        print("   Downloading from Hugging Face...")
        print("   (Model size ~50–100 MB, should be quick)")

        # Download model (spkrec-ecapa-voxceleb is public; token only needed if set)
        EncoderClassifier.from_hparams(
            source=model_repo,
            savedir=local_dir,
            use_auth_token=hf_token if hf_token else False
        )

        print("✅ Successfully downloaded ECAPA Voiceprint model")
        return True

    except Exception as e:
        print(f"❌ Failed to download ECAPA Voiceprint model: {e}")
        print("   Possible fixes:")
        print("   1. Check internet connectivity")
        print("   2. Verify Hugging Face access")
        print("   3. Clear cache and retry")
        return False

def main():
    """Download all models"""
    print("\n" + "="*70)
    print("🚀 Zaban Model Downloader")
    print("="*70)
    print(f"HuggingFace cache: {os.getenv('HF_HOME', Path.home() / '.cache/huggingface')}")
    print(f"Whisper cache: {Path.home() / '.cache/whisper'}")
    print(f"FastText cache: {os.getenv('FASTTEXT_CACHE_DIR', Path.home() / '.cache/zaban/models')}")
    print(f"HF Token set: {'Yes' if os.getenv('HUGGING_FACE_TOKEN') else 'No'}")
    print("="*70)

    results = {
        "IndicTrans2": download_indictrans2_models(),
        "IndicParler TTS": download_indicparler_tts_model(),
        "Whisper STT": download_whisper_model(),
        "FastText": download_fasttext_model(),
        "Voiceprint": download_voiceprint_models(),
    }

    # Summary
    print("\n" + "="*70)
    print("📊 Download Summary")
    print("="*70)
    for model, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {model}")

    # Exit with error if any critical model failed
    critical_failures = [k for k, v in results.items() if not v and k != "IndicParler TTS"]
    if critical_failures:
        print(f"\n❌ Critical models failed: {', '.join(critical_failures)}")
        print("   Build will continue, but these models will be downloaded at runtime.")
        # Don't fail the build, just warn
        return 0

    if not results["IndicParler TTS"]:
        print("\n⚠️  IndicParler TTS not downloaded (requires HF token and access)")
        print("   This model will be downloaded at runtime if HUGGING_FACE_TOKEN is set.")
        # Don't fail the build for TTS
        return 0

    print("\n✅ All models downloaded successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
