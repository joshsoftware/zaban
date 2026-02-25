# Zaban Backend (FastAPI)

This is the backend for the Zaban platform, built with Python FastAPI. It handles authentication (Google SSO), API key management, and proxies requests to AI4Bharat services (TTS, STT, Translation, Transliteration).

## Prerequisites

*   Python 3.10+
*   [uv](https://github.com/astral-sh/uv) (Fast Python package manager)
*   PostgreSQL 14+

## Local Development Setup

### 1. Installation

Install dependencies using `uv` (uses `uv.lock` for reproducible installs):

```bash
# Recommended: create venv first, then sync from lockfile
uv venv
uv sync

# Or, install in editable mode without using the lockfile
uv venv
source .venv/bin/activate
uv pip install -e .
```

To **add a new dependency**, prefer letting `uv` update both `pyproject.toml` and `uv.lock` for you:

```bash
uv add PACKAGE_NAME
```

This will update `pyproject.toml` and refresh `uv.lock` in one step.

If you edit `pyproject.toml` manually, or want to refresh the lockfile, run **`uv lock`** and commit `uv.lock`. You can do that **via Docker** (no local uv needed) from the **repo root**:

```bash
docker compose run --rm -v "$(pwd)/zaban_backend:/app" -w /app backend uv lock
```

Then commit the updated `zaban_backend/uv.lock` and rebuild.

### 2. Environment Configuration

Create a `.env` file in the `zaban_backend` directory by copying the example:

```bash
cp .env.example .env
```

### 3. Database Setup

Ensure PostgreSQL is running, then create the database and run migrations:

```bash
# Create database
createdb zaban_backend_development

# Run migrations
uv run alembic upgrade head
```

### 4. Run the Server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

*   **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Docker

To run the backend as a container:

```bash
docker build -t zaban-backend .
docker run -p 8000:8000 --env-file .env zaban-backend
```

*Note: Use the root `docker-compose.yml` to run with the database automatically linked.*

## API Endpoints Overview

### Auth
*   `POST /api/v1/auth/google/login`: Exchange Google code for JWT.
*   `GET /api/v1/auth/me`: Get current user profile.

### API Keys
*   `POST /api/v1/api-keys`: Create a new API key.
*   `GET /api/v1/api-keys`: List keys.

### AI Services (Require `X-API-Key` header)
*   `POST /api/v1/tts`: Text-to-Speech.
*   `POST /api/v1/stt`: Speech-to-Text.
*   `POST /api/v1/translate`: Translation.
*   `POST /api/v1/transliterate`: Transliteration.

## Detailed Usage & Examples

### Translation (English to Hindi)

```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-your-secret-key-here" \
  -d '{"text":"How are you?","source_lang":"eng_Latn","target_lang":"hin_Deva"}'
```

### Authentication Flow (Google SSO)

1.  **Get Code**: Redirect user to Google OAuth URL.
2.  **Exchange Code**: POST the received code to `/api/v1/auth/google/login`.
3.  **Use Token**: Use the returned JWT in the `Authorization: Bearer <token>` header.

### Supported Languages (IndicTrans2)

Includes `eng_Latn` (English) and 22 Indian languages (e.g., `hin_Deva`, `tam_Taml`, `tel_Telu`). See full documentation for the comprehensive list of BCP-47 codes.

## Testing

Run the test suite:

```bash
uv run pytest -q
```
