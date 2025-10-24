Zabaan Backend (FastAPI)

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

# IndicTrans2 Translation (uses local model by default)
USE_LOCAL_INDICTRANS2=true
INDICTRANS2_AUTO_LOAD=false  # Set to true to load models at startup (faster first request but slower startup)
INDICTRANS2_EN_INDIC_MODEL=ai4bharat/indictrans2-en-indic-dist-200M  # 200M distilled model
INDICTRANS2_INDIC_EN_MODEL=ai4bharat/indictrans2-indic-en-dist-200M

# AI4Bharat endpoints (optional, for TTS/STT/Transliteration or external translation API)
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

API Key Management Endpoints

- POST `/api/v1/api-keys` - Create API key (requires Bearer token)
- GET `/api/v1/api-keys` - List user's API keys (requires Bearer token)
- GET `/api/v1/api-keys/{key_id}` - Get specific API key details (requires Bearer token)
- DELETE `/api/v1/api-keys/{key_id}` - Delete API key (requires Bearer token)

AI4Bharat Endpoints (All require X-API-Key header)

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

## API Key Management Flow

All AI4Bharat services now require API key authentication. Here's the complete flow:

### 1. Create API Key

```bash
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key"}'

# Response:
# {
#   "id": "uuid-here",
#   "name": "My API Key",
#   "secret_key": "sk-ewVR1t_HMn57DRmVu..."
# }
```

### 2. List Your API Keys

```bash
curl -X GET http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response:
# {
#   "api_keys": [
#     {
#       "id": "uuid-here",
#       "name": "My API Key",
#       "is_active": true,
#       "created_at": "2025-10-23T06:59:12",
#       "revoked_at": null
#     }
#   ],
#   "total": 1
# }
```

### 3. Get Specific API Key Details

```bash
curl -X GET http://localhost:8000/api/v1/api-keys/{API_KEY_ID} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Delete API Key

```bash
curl -X DELETE http://localhost:8000/api/v1/api-keys/{API_KEY_ID} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## API Key Security Features

- **User Isolation**: Each user can only see and manage their own API keys
- **Secret Key Format**: All API keys start with `sk-` prefix
- **One-time Display**: Raw secret keys are only shown once during creation
- **Secure Storage**: Keys are hashed and stored securely in the database
- **Deactivation**: Deleted keys are permanently unusable

## Complete Testing Flow

Here's a step-by-step guide to test the entire API:

### Step 1: Start the Server
```bash
set -a && [ -f .env ] && . ./.env && set +a
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Get Google OAuth Code
Open this URL in your browser (replace with your actual client ID):
```
https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8000/auth/callback&response_type=code&scope=openid%20email%20profile&prompt=consent&login_hint=your.email@joshsoftware.com
```

### Step 3: Exchange Code for JWT Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/google/login \
  -H "Content-Type: application/json" \
  -d '{"code":"PASTE_YOUR_CODE_HERE","redirect_uri":"http://localhost:8000/auth/callback"}'
```

### Step 4: Create API Key
```bash
# Save the JWT token from step 3
JWT_TOKEN="your_jwt_token_here"

curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Key"}'

# Save the secret_key from the response
SECRET_KEY="sk-your-secret-key-here"
```

### Step 5: Test Translation with API Key
```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SECRET_KEY" \
  -d '{"text":"Hello, how are you?","source_lang":"eng_Latn","target_lang":"hin_Deva"}'
```

### Step 6: List Your API Keys
```bash
curl -X GET http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Step 7: Test Other Services
```bash
# TTS
curl -X POST http://localhost:8000/api/v1/tts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SECRET_KEY" \
  -d '{"text":"नमस्ते","lang":"hi","speaker":"female"}'

# STT (if you have an audio file)
curl -X POST http://localhost:8000/api/v1/stt \
  -H "X-API-Key: $SECRET_KEY" \
  -F "audio=@/path/to/audio.wav" -F "lang=hi"

# Transliteration
curl -X POST http://localhost:8000/api/v1/transliterate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SECRET_KEY" \
  -d '{"text":"namaste","source_script":"latn","target_script":"deva","lang":"hi"}'
```

Example AI4Bharat Requests

Translation (IndicTrans2)

The translation endpoint uses the local IndicTrans2 model by default. It supports 22 Indian languages.

**Language Codes (BCP-47 format with script):**
- English: `eng_Latn`
- Hindi: `hin_Deva`
- Bengali: `ben_Beng`
- Telugu: `tel_Telu`
- Tamil: `tam_Taml`
- Gujarati: `guj_Gujr`
- Kannada: `kan_Knda`
- Malayalam: `mal_Mlym`
- Marathi: `mar_Deva`
- Punjabi: `pan_Guru`
- Oriya: `ory_Orya`
- Assamese: `asm_Beng`
- Urdu: `urd_Arab`
- Kashmiri (Arabic): `kas_Arab`
- Kashmiri (Devanagari): `kas_Deva`
- Konkani: `gom_Deva`
- Manipuri (Bengali): `mni_Beng`
- Manipuri (Meitei): `mni_Mtei`
- Nepali: `npi_Deva`
- Sanskrit: `san_Deva`
- Santali: `sat_Olck`
- Sindhi (Arabic): `snd_Arab`
- Sindhi (Devanagari): `snd_Deva`

**English to Hindi:**
```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-your-secret-key-here" \
  -d '{"text":"How are you?","source_lang":"eng_Latn","target_lang":"hin_Deva"}'

# Response:
# {
#   "translated_text": "आप कैसे हैं?",
#   "source_lang": "eng_Latn",
#   "target_lang": "hin_Deva",
#   "model": "indictrans2-local"
# }
```

**Hindi to English:**
```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-your-secret-key-here" \
  -d '{"text":"आप कैसे हैं?","source_lang":"hin_Deva","target_lang":"eng_Latn"}'
```

**English to Tamil:**
```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-your-secret-key-here" \
  -d '{"text":"Good morning","source_lang":"eng_Latn","target_lang":"tam_Taml"}'
```

**Note:** On the first translation request, the models will be downloaded (~ 800MB total). This may take a few minutes. Subsequent requests will be fast.

TTS

```bash
curl -X POST http://localhost:8000/api/v1/tts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-your-secret-key-here" \
  -d '{"text":"नमस्ते दुनिया","lang":"hi","speaker":"female","sample_rate":22050,"format":"wav"}'
```

```bash
curl -X POST http://localhost:8000/api/v1/transliterate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-your-secret-key-here" \
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
- Do not include PKCE parameters (code_challenge) in the authorization URL - PKCE is not needed for server-side web applications with client secrets (confidential clients)

Database connection errors

- Ensure PostgreSQL is running: `pg_isready`
- Create database if missing: `createdb zaban_backend_development`
- Verify DATABASE_URL format: `postgresql+psycopg://user:password@host:port/dbname`

API Key Authentication Errors

- **401 Unauthorized**: Missing or invalid X-API-Key header
- **401 Invalid or inactive API key**: API key doesn't exist or has been deactivated
- **401 X-API-Key header missing**: No API key provided in request

Common API Key Issues:
- Ensure API key starts with `sk-` prefix
- Check that the API key hasn't been deleted/deactivated
- Verify the X-API-Key header is included in all AI4Bharat service requests
- API keys are user-specific - you can only use keys you created
OAuth Security Notes

- **PKCE (Proof Key for Code Exchange)**: This application uses a server-side OAuth flow with client secrets (confidential client), so PKCE is not required. PKCE is primarily for public clients (mobile apps, SPAs) that cannot securely store client secrets.
- **Client Type**: Configure as "Web application" in Google Cloud Console (not "Desktop" or "Mobile")
- **Security**: The application uses client secrets for authentication, which is appropriate for server-side applications

Notes

- AI4Bharat model docs: https://github.com/AI4Bharat/IndicTrans2 and https://ai4bharat.iitm.ac.in/
- Postman collections available in `docs/postman/`
- The app uses an in-memory token denylist for logout (use Redis in production)
- Domain allow-list defaults to joshsoftware.com (configure via ALLOWED_SSO_DOMAINS)
- All endpoints automatically load .env on startup via `load_dotenv(override=True)` in app/main.py
