Zabaan Backend (Rails 8)

This is the Rails 8 API backend for Zabaan. It provides authentication, API key management, and AI feature endpoints (TTS, STT, Translation, Transliteration).

Prerequisites

- Ruby (3.3+) and Bundler
- PostgreSQL (14+)
- Node.js (for asset tooling if needed) and Yarn/npm
- Redis (if you plan to run background jobs or Action Cable in dev)

Setup

1) Install Ruby gems

```
bundle install
```

2) Configure environment

Create `.env` or use your shell export mechanism. At minimum, you will need:

```
RAILS_ENV=development
DATABASE_URL=postgres://<user>:<password>@localhost:5432/zabaan_dev
RAILS_MASTER_KEY=<your-master-key-if-using-credentials>
JWT_SECRET=<a-long-random-secret>
```

Alternatively, configure `config/database.yml` with local credentials. Ensure PostgreSQL is running and accessible.

3) Prepare database

```
bin/rails db:create db:migrate
```

4) Seed data (optional)

```
bin/rails db:seed
```

Run the Server

```
bin/rails server
```

By default it will serve on `http://localhost:3000`.

Environment & Credentials

- Credentials are managed via Rails encrypted credentials. To edit:

```
bin/rails credentials:edit
```

- Ensure `config/credentials.yml.enc` and the master key are properly set for your environment.

Common Commands

- Run console: `bin/rails console`
- Run migrations: `bin/rails db:migrate`
- Rollback last migration: `bin/rails db:rollback`
- Lint (if configured): `bin/rubocop`
- Security scan (if configured): `bin/brakeman`

Testing

- If you use RSpec or Minitest, run the suite with:

```
bin/rake test
```

API Keys and Authentication

- Users authenticate via email/password to obtain tokens (JWT/Devise).
- API requests require an `Authorization: Bearer <API_KEY>` header.
- Keys can be issued, rotated, and revoked from the dashboard (or Admin panel).

Deployment Notes

- See `Dockerfile` and `bin/kamal` (if using Kamal) for containerized deploys.
- Ensure environment variables and credentials are configured in the target environment.
