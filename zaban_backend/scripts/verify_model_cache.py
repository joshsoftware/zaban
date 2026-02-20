#!/usr/bin/env python3
"""
Verify that all models are present in cache and won't download at runtime.
"""
import os
from pathlib import Path


def check_cache_directory(path, name):
    """Check if a cache directory exists and has content"""
    path = Path(path)
    exists = path.exists()
    has_content = exists and any(path.iterdir()) if exists else False

    status = "✅" if has_content else "❌"
    print(f"{status} {name}: {path}")

    if exists and has_content:
        # Show size
        total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f"   Size: {size_mb:.2f} MB")
    elif exists:
        print(f"   ⚠️  Directory exists but is empty")
    else:
        print(f"   ⚠️  Directory does not exist")

    return has_content


def main():
    print("\n" + "="*70)
    print("🔍 Model Cache Verification")
    print("="*70 + "\n")

    # Check HuggingFace cache
    hf_home = os.getenv("HF_HOME", Path.home() / ".cache/huggingface")
    hf_hub = Path(hf_home) / "hub"

    print("📦 HuggingFace Models:")
    models_ok = True

    # Check specific models
    expected_models = [
        "models--ai4bharat--indictrans2-en-indic-dist-200M",
        "models--ai4bharat--indictrans2-indic-en-dist-200M",
        "models--ai4bharat--indic-parler-tts",
    ]

    for model_dir in expected_models:
        model_path = hf_hub / model_dir
        exists = model_path.exists() and any(model_path.iterdir())
        status = "✅" if exists else "❌"
        model_name = model_dir.replace("models--", "").replace("--", "/")
        print(f"   {status} {model_name}")
        if not exists:
            models_ok = False

    # Check Whisper cache
    print("\n📦 Whisper Model:")
    whisper_cache = Path.home() / ".cache/whisper"
    whisper_model = os.getenv("WHISPER_MODEL", "medium")
    whisper_file = whisper_cache / f"{whisper_model}.pt"

    whisper_ok = check_cache_directory(whisper_cache, f"Whisper ({whisper_model})")
    if whisper_cache.exists():
        if whisper_file.exists():
            print(f"   ✅ Model file: {whisper_file.name}")
        else:
            print(f"   ❌ Model file not found: {whisper_file.name}")
            whisper_ok = False

    # Check FastText cache
    print("\n📦 FastText Model:")
    fasttext_cache = Path(os.getenv("FASTTEXT_CACHE_DIR", Path.home() / ".cache/zaban/models"))
    fasttext_file = fasttext_cache / "lid.176.bin"

    fasttext_ok = check_cache_directory(fasttext_cache, "FastText")
    if fasttext_cache.exists():
        if fasttext_file.exists():
            print(f"   ✅ Model file: {fasttext_file.name}")
        else:
            print(f"   ❌ Model file not found: {fasttext_file.name}")
            fasttext_ok = False

    # Summary
    print("\n" + "="*70)
    print("📊 Summary")
    print("="*70)

    all_ok = models_ok and whisper_ok and fasttext_ok

    if all_ok:
        print("✅ All models are cached and ready!")
        print("   No downloads will occur at runtime.")
        return 0
    else:
        print("⚠️  Some models are missing from cache.")
        print("   These will be downloaded at runtime on first use.")
        if not models_ok:
            print("   - Missing: HuggingFace models")
        if not whisper_ok:
            print("   - Missing: Whisper model")
        if not fasttext_ok:
            print("   - Missing: FastText model")
        return 1


if __name__ == "__main__":
    exit(main())
