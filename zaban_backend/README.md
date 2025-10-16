Zabaan Backend (FastAPI)

This repository now uses Python FastAPI for the backend and for wrapping AI4Bharat services (TTS, STT, Translation, Transliteration).

Prerequisites

- Python 3.11
- uv (Python package manager)

Setup

1) Create a virtual environment and install dependencies

```
cd fastapi_app
uv venv
. .venv/bin/activate
uv pip install fastapi uvicorn[standard] httpx python-multipart pydantic pydantic-settings
```

2) Configure environment

Set the AI4Bharat service endpoints (public endpoints typically do not need keys):

```
export AI4B_TRANSLATE_URL="https://<your-indictrans2-endpoint>"
export AI4B_TTS_URL="https://<your-indicparler-tts-endpoint>"
export AI4B_STT_URL="https://<your-stt-endpoint>"            # or set AI4B_OPEN_SPEECH_URL
export AI4B_TRANSLITERATE_URL="https://<your-indic-xlit-endpoint>"
# Optional keys (leave unset if not required)
export AI4B_API_KEY=""
export AI4B_OPEN_SPEECH_API_KEY=""
```

Run the Server

```
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints

- POST `/api/v1/tts`
- POST `/api/v1/stt` (multipart file upload or JSON with `audio_url`)
- POST `/api/v1/translate`
- POST `/api/v1/transliterate`

Example Requests

TTS

```
curl -X POST http://localhost:8000/api/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"नमस्ते दुनिया","lang":"hi","speaker":"female","sample_rate":22050,"format":"wav"}'
```

STT (multipart)

```
curl -X POST http://localhost:8000/api/v1/stt \
  -F "audio=@/path/to/sample.wav" -F "lang=hi" -F "format=wav"
```

STT (audio_url JSON)

```
curl -X POST http://localhost:8000/api/v1/stt \
  -H "Content-Type: application/json" \
  -d '{"audio_url":"https://example.com/sample.wav","lang":"hi","format":"wav"}'
```

Translate

```
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{"text":"How are you?","source_lang":"en","target_lang":"hi"}'
```

Transliterate

```
curl -X POST http://localhost:8000/api/v1/transliterate \
  -H "Content-Type: application/json" \
  -d '{"text":"namaste","source_script":"latn","target_script":"deva","lang":"hi","topk":3}'
```

Notes

- AI4Bharat repos and model documentation: `https://github.com/AI4Bharat/IndicTrans2` and `https://ai4bharat.iitm.ac.in/`.
- If endpoints are public, you can omit API keys. Restart the server after changing env vars.
