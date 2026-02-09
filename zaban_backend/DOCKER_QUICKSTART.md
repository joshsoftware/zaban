# Docker Quick Start Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

## Quick Start

1. **Navigate to the backend directory:**
   ```bash
   cd zaban_backend
   ```

2. **Create a `.env` file** (optional, for custom configuration):
   ```bash
   # Minimum required variables:
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   JWT_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(64))')
   ```

3. **Start the services:**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations:**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Access the application:**
   - API: http://localhost:8000
   - Health check: http://localhost:8000/up
   - API docs: http://localhost:8000/docs

## Common Commands

```bash
# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Run migrations
docker-compose exec backend alembic upgrade head

# Access backend shell
docker-compose exec backend bash

# View database
docker-compose exec db psql -U postgres -d zaban_backend

# Restart services
docker-compose restart
```

## Environment Variables

The `docker-compose.yml` includes default values for most settings. You can override them by:

1. Creating a `.env` file in the `zaban_backend` directory
2. Setting environment variables in your shell before running `docker-compose`

### Required Variables

- `GOOGLE_CLIENT_ID` - Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Your Google OAuth client secret
- `JWT_SECRET` - A secure random string (generate with: `python -c 'import secrets; print(secrets.token_urlsafe(64))'`)

### Optional Variables

- `ALLOWED_SSO_DOMAINS` - Comma-separated list of allowed email domains
- `INDICTRANS2_AUTO_LOAD` - Set to `true` to preload models at startup
- `PRELOAD_WHISPER` - Set to `true` to preload Whisper model
- AI4Bharat API keys and URLs (if using external APIs)

## Model Downloads

Models are automatically downloaded on first use:
- **IndicTrans2**: ~800MB (from HuggingFace)
- **FastText**: ~126MB (from Facebook AI)

Models are cached in Docker volumes and persist between container restarts.

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs backend

# Check if port 8000 is already in use
lsof -i :8000
```

### Database connection errors

```bash
# Check if database is healthy
docker-compose ps

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Models not downloading

```bash
# Check network connectivity
docker-compose exec backend curl -I https://huggingface.co

# Manually trigger model download by making a translation request
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"text":"Hello","source_lang":"eng_Latn","target_lang":"hin_Deva"}'
```

### Permission errors

```bash
# Fix volume permissions (if needed)
docker-compose down
sudo chown -R $USER:$USER .
docker-compose up -d
```

## Production Considerations

1. **Use environment-specific `.env` files** - Don't commit `.env` to git
2. **Set strong `JWT_SECRET`** - Use a long, random string
3. **Configure proper CORS** - Update `allow_origins` in `app/main.py`
4. **Use managed PostgreSQL** - Consider RDS, Cloud SQL, or managed database service
5. **Enable SSL/HTTPS** - Use a reverse proxy (nginx, traefik) with Let's Encrypt
6. **Monitor resource usage** - ML models require significant RAM
7. **Backup database** - Set up regular backups for PostgreSQL

## Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (deletes database and model cache)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

