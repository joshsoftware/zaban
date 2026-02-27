# Dev Dockerfile: CPU only. For GPU use Dockerfile.prod (e.g. with docker-compose.prod.yml).
FROM ubuntu:22.04

# Avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies + Python 3.11 (python3.11-dev for C extension builds, e.g. IndicTransToolkit)
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    gcc \
    g++ \
    curl \
    postgresql-client \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Make python3.11 the default python
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy dependency files and app
COPY pyproject.toml uv.lock ./

# Copy application code (needed for editable install)
COPY . .

# Create venv and install dependencies using uv.lock
RUN uv venv && \
    . .venv/bin/activate && \
    uv sync --frozen --no-dev

# Create directory for ML models cache
RUN mkdir -p /app/.cache/huggingface
RUN mkdir -p /root/.cache/zaban/models

# Set environment variables
ENV PYTHONUNBUFFERED=1
# HuggingFace model cache (IndicTrans2, IndicParler TTS)
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV HF_HOME=/app/.cache/huggingface
# Whisper model cache
ENV XDG_CACHE_HOME=/root/.cache
# FastText model cache
ENV FASTTEXT_CACHE_DIR=/root/.cache/zaban/models

# Build argument for Hugging Face token (for gated models)
ARG HUGGING_FACE_TOKEN
ENV HUGGING_FACE_TOKEN=${HUGGING_FACE_TOKEN}

# Pre-download ML models during build (optional; will retry at runtime if needed)
RUN . .venv/bin/activate && \
    python scripts/download_models.py || echo "⚠️  Some models failed to download, will retry at runtime"

# Expose port 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/up || exit 1

# Run database migrations and start the server
CMD ["/bin/bash", "-c", ". .venv/bin/activate && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]