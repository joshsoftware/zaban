Zaban

Zaban is a SaaS platform offering AI-powered APIs for Text-to-Speech (TTS), Speech-to-Text (STT), Translation, and Transliteration. Users can sign up, generate API keys, and integrate these capabilities into their apps with minimal friction.

Think of it like an easy-to-integrate alternative to similar AI platforms, with a focus on developer experience.

Key Features

- User accounts with email/password sign-in, password recovery, and profile management
- API key issuance, rotation, and revocation
- AI endpoints for:
  - Text-to-Speech (TTS): generate natural-sounding audio from text
  - Speech-to-Text (STT): transcribe audio to text
  - Translation: convert text between languages
  - Transliteration: convert text between scripts while preserving pronunciation

Architecture

- Backend: Ruby on Rails 8 (PostgreSQL, JWT/Devise authentication)
- Frontend: Next.js dashboard for profile, API keys, and usage analytics
- Providers: Integrations with AI4Bharat, OpenAI, and others

Monorepo Layout

- `zaban_backend/`: Rails 8 API backend
  - See `zaban_backend/README.md` for setup and local development
- (Planned) `zaban_frontend/`: Next.js dashboard

Quick Start

1) Backend setup

- Ensure you have Ruby, Bundler, PostgreSQL installed
- See `zaban_backend/README.md` for full instructions

2) Using the APIs

- Sign up, create an API key in the dashboard (TBD)
- Call REST endpoints with the header `Authorization: Bearer <API_KEY>`

Status

- Active development. Contributions and feedback are welcome.
