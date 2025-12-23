# Zaban

Zaban is a SaaS platform offering AI-powered APIs for Text-to-Speech (TTS), Speech-to-Text (STT), Translation, and Transliteration. It focuses on developer experience, allowing users to sign up, generate API keys, and integrate capabilities into their apps.

## Architecture

*   **Backend**: Python FastAPI (with SQLAlchemy, Alembic, PostgreSQL)
*   **Frontend**: Next.js (React, Tailwind CSS)
*   **Database**: PostgreSQL
*   **Infrastructure**: Docker & Docker Compose

## Repository Structure

*   `zaban_backend/`: The FastAPI backend application.
*   `frontend/`: The Next.js frontend dashboard.
*   `docker-compose.yml`: Root Docker Compose configuration for orchestrating the services.

## Quick Start (Docker)

The easiest way to run the entire stack is using Docker Compose.

### Prerequisites

*   Docker
*   Docker Compose

### 1. Configure Environment Variables

This project relies on environment variables for configuration. You need to set up `.env` files for both the frontend and backend.

**Backend (`zaban_backend/.env`):**

Copy `zaban_backend/.env.example` to `zaban_backend/.env`:
```bash
cp zaban_backend/.env.example zaban_backend/.env
```

**Frontend (`frontend/.env`):**

Copy `frontend/.env.example` to `frontend/.env`:
```bash
cp frontend/.env.example frontend/.env
```

### 2. Run with Docker Compose

Build and start the services:

```bash
docker-compose up --build
```

This will start:
*   **Postgres**: `localhost:5432`
*   **Backend**: `localhost:8000`
*   **Frontend**: `localhost:3000`

## Manual Setup

If you prefer to run services individually without Docker, please refer to the specific READMEs:

*   [Backend Setup Guide](./zaban_backend/README.md)
*   [Frontend Setup Guide](./frontend/README.md)

## Key Features

*   **Authentication**: Google SSO integration.
*   **API Management**: Issue, rotate, and revoke API keys via the dashboard.
*   **AI Services**:
    *   **Text-to-Speech (TTS)**: Generate natural-sounding audio.
    *   **Speech-to-Text (STT)**: Transcribe audio to text.
    *   **Translation**: Translate text between supported languages.
    *   **Transliteration**: Convert text between scripts.

## License

Private repository. All rights reserved.