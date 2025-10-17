Zaban Backend (FastAPI)

This repository uses Python FastAPI for the backend with Google SSO authentication and AI4Bharat services (TTS, STT, Translation, Transliteration).

Prerequisites

- Python 3.11
- uv (Python package manager)
- PostgreSQL 14+

Setup

1) Install dependencies

```bash
uv venv
. .venv/bin/activate
uv pip install -e .
```

2) Configure environment

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/zaban_backend_development

# Google OAuth (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Auth
JWT_SECRET=your-long-random-secret-string
ALLOWED_SSO_DOMAINS=joshsoftware.com

# AI4Bharat endpoints (optional, configure when ready)
AI4B_TRANSLATE_URL=
AI4B_TTS_URL=
AI4B_STT_URL=
AI4B_TRANSLITERATE_URL=
AI4B_API_KEY=
AI4B_OPEN_SPEECH_API_KEY=
```

Generate a secure JWT secret:
```bash
python -c 'import secrets; print(secrets.token_urlsafe(64))'
```

3) Database setup

```bash
createdb zaban_backend_development
uv run alembic upgrade head
```

Run the Server

The app automatically loads `.env` on startup:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If .env is not loading properly, manually load it first:

```bash
set -a && [ -f .env ] && . ./.env && set +a
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify environment variables are loaded:

```bash
uv run python -c 'from dotenv import load_dotenv; load_dotenv(override=True); import os; print(os.getenv("GOOGLE_CLIENT_ID"), bool(os.getenv("GOOGLE_CLIENT_SECRET")))'
```

You should see your Google Client ID and `True`.

Run Tests

```bash
uv run pytest -q
```

Endpoints

Auth Endpoints

- POST `/api/v1/auth/google/login` - Google SSO login
- GET `/api/v1/auth/me` - Get current user (requires Bearer token)
- POST `/api/v1/auth/logout` - Logout (invalidates token)

AI4Bharat Endpoints

- POST `/api/v1/tts` - Text to Speech
- POST `/api/v1/stt` - Speech to Text (multipart file upload or JSON with audio_url)
- POST `/api/v1/translate` - Translation
- POST `/api/v1/transliterate` - Transliteration

Example Auth Flow

1. Get authorization code from Google (open in browser):

```
https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8000/auth/callback&response_type=code&scope=openid%20email%20profile&prompt=consent&login_hint=your.email@joshsoftware.com
```

2. Exchange code for token (copy the decoded code from redirect, NOT the URL-encoded version):

```bash
curl -X POST http://localhost:8000/api/v1/auth/google/login \
  -H "Content-Type: application/json" \
  -d '{"code":"PASTE_DECODED_CODE_HERE","redirect_uri":"http://localhost:8000/auth/callback"}'
```

3. Use the returned token:

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

4. Logout:

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Example AI4Bharat Requests

TTS

```bash
curl -X POST http://localhost:8000/api/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"नमस्ते दुनिया","lang":"hi","speaker":"female","sample_rate":22050,"format":"wav"}'
```

STT (multipart)

```bash
curl -X POST http://localhost:8000/api/v1/stt \
  -F "audio=@/path/to/sample.wav" -F "lang=hi" -F "format=wav"
```

STT (audio_url JSON)

```bash
curl -X POST http://localhost:8000/api/v1/stt \
  -H "Content-Type: application/json" \
  -d '{"audio_url":"https://example.com/sample.wav","lang":"hi","format":"wav"}'
```

Translate

```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{"text":"How are you?","source_lang":"en","target_lang":"hi"}'
```

Transliterate

```bash
curl -X POST http://localhost:8000/api/v1/transliterate \
  -H "Content-Type: application/json" \
  -d '{"text":"namaste","source_script":"latn","target_script":"deva","lang":"hi","topk":3}'
```

Troubleshooting

Environment variables not loading

If the server doesn't see your .env variables:

1. Verify .env exists in project root:
```bash
cat .env | grep GOOGLE_CLIENT_ID
```

2. Manually load before starting server:
```bash
set -a && source .env && set +a
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Check if app sees the variables:
```bash
uv run python -c 'from dotenv import load_dotenv; load_dotenv(override=True); import os; print(os.getenv("GOOGLE_CLIENT_ID"))'
```

Google OAuth invalid_grant error

- Use a fresh authorization code (codes expire in ~10 minutes and are single-use)
- **IMPORTANT**: Copy the DECODED code from the redirect URL. If you see `4%2F0AVG...` in the browser, decode it to `4/0AVG...` before POSTing
- Ensure redirect_uri is EXACTLY the same in:
  - Browser authorization URL
  - POST request body
  - Google Cloud Console (Authorized redirect URIs)
- Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are loaded in the server process
- Ensure OAuth client type is "Web application" (not "Desktop" or "Mobile")
- Add your Google account as a test user if consent screen is in "Testing" mode
- Do not include PKCE parameters (code_challenge) in the authorization URL

Database connection errors

- Ensure PostgreSQL is running: `pg_isready`
- Create database if missing: `createdb zaban_backend_development`
- Verify DATABASE_URL format: `postgresql+psycopg://user:password@host:port/dbname`

Notes

- AI4Bharat model docs: https://github.com/AI4Bharat/IndicTrans2 and https://ai4bharat.iitm.ac.in/
- Postman collections available in `docs/postman/`
- The app uses an in-memory token denylist for logout (use Redis in production)
- Domain allow-list defaults to joshsoftware.com (configure via ALLOWED_SSO_DOMAINS)
- All endpoints automatically load .env on startup via `load_dotenv(override=True)` in app/main.py
